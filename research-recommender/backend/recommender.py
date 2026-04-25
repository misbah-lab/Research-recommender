import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import faiss

DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent / "models"
FEEDBACK_FILE = MODELS_DIR / "feedback.json"

class RecommendationEngine:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None
        self.df = None
        self.embeddings = None
        self.index = None
        self.is_loaded = False
        self.total_papers = 0
        self.feedback: Dict[str, int] = {}
        self._load_feedback()

    def load(self):
        """Load model, dataset, and pre-built embeddings (or build them)."""
        print("[1/4] Loading SentenceTransformer model...")
        self.model = SentenceTransformer(self.model_name)

        print("[2/4] Loading dataset...")
        csv_path = DATA_DIR / "arxiv_data.csv"
        parquet_path = DATA_DIR / "arxiv_data.parquet"
        json_path = DATA_DIR / "arxiv-metadata-oai-snapshot.json"

        if parquet_path.exists():
            self.df = pd.read_parquet(parquet_path)
        elif csv_path.exists():
            self.df = pd.read_csv(csv_path)
        elif json_path.exists():
            # arXiv raw JSON — load line by line
            records = []
            print("  Parsing arXiv JSON (this may take a moment)...")
            with open(json_path, "r") as f:
                for i, line in enumerate(f):
                    if i >= 200_000:   # cap at 200k for memory
                        break
                    try:
                        r = json.loads(line)
                        records.append({
                            "id": r.get("id", ""),
                            "title": r.get("title", "").replace("\n", " ").strip(),
                            "abstract": r.get("abstract", "").replace("\n", " ").strip(),
                            "authors": r.get("authors", ""),
                            "categories": r.get("categories", ""),
                            "update_date": r.get("update_date", ""),
                        })
                    except Exception:
                        continue
            self.df = pd.DataFrame(records)
            # save as parquet for fast reloads
            self.df.to_parquet(parquet_path, index=False)
        else:
            raise FileNotFoundError(
                "No dataset found in /data folder.\n"
                "Expected one of: arxiv_data.csv, arxiv_data.parquet, "
                "or arxiv-metadata-oai-snapshot.json"
            )

        # Normalize column names to what the rest of the code expects
        col_map = {}
        if "summary" in self.df.columns and "abstract" not in self.df.columns:
            col_map["summary"] = "abstract"
        if "category" in self.df.columns and "categories" not in self.df.columns:
            col_map["category"] = "categories"
        if "updated_date" in self.df.columns and "update_date" not in self.df.columns:
            col_map["updated_date"] = "update_date"
        if col_map:
            self.df.rename(columns=col_map, inplace=True)

        # Drop rows with empty title/abstract
        self.df.dropna(subset=["title", "abstract"], inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        self.total_papers = len(self.df)
        print(f"  Loaded {self.total_papers:,} papers.")

        print("[3/4] Loading / building embeddings...")
        emb_path = MODELS_DIR / "embeddings.npy"
        if emb_path.exists():
            self.embeddings = np.load(str(emb_path))
            print("  Embeddings loaded from cache.")
        else:
            print("  Building embeddings (first run — may take several minutes)...")
            texts = (self.df["title"] + " " + self.df["abstract"]).tolist()
            self.embeddings = self.model.encode(
                texts, batch_size=256, show_progress_bar=True,
                convert_to_numpy=True, normalize_embeddings=True
            )
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            np.save(str(emb_path), self.embeddings)
            print("  Embeddings saved.")

        print("[4/4] Building FAISS index...")
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)   # Inner product = cosine when normalized
        self.index.add(self.embeddings.astype("float32"))

        self.is_loaded = True
        print("Engine ready.")

    def recommend(self, query: str, top_n: int = 10, domain_filter: Optional[str] = None) -> List[dict]:
        query_emb = self.model.encode([query], normalize_embeddings=True).astype("float32")
        k = min(top_n * 5, self.total_papers)   # over-fetch for filtering
        scores, indices = self.index.search(query_emb, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            row = self.df.iloc[idx]
            cats = str(row.get("categories", ""))
            if domain_filter and domain_filter.lower() not in cats.lower():
                continue

            # Extract year
            date = str(row.get("update_date", ""))
            year = date[:4] if date else ""

            results.append({
                "id": str(row.get("id", idx)),
                "title": str(row.get("title", "N/A")),
                "abstract": str(row.get("abstract", ""))[:600] + "...",
                "authors": str(row.get("authors", "N/A")),
                "categories": cats,
                "match_score": round(float(score) * 100, 2),
                "year": year,
            })
            if len(results) >= top_n:
                break

        return results

    def get_domains(self) -> List[str]:
        if self.df is None:
            return []
        all_cats = self.df["categories"].dropna().str.split().explode()
        return sorted(all_cats.value_counts().head(40).index.tolist())

    def record_feedback(self, paper_id: str, relevant: bool):
        self.feedback[paper_id] = 1 if relevant else 0
        self._save_feedback()

    def _load_feedback(self):
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE) as f:
                self.feedback = json.load(f)

    def _save_feedback(self):
        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(self.feedback, f)