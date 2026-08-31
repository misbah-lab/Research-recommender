import os
import json
import ssl
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODELS_DIR = Path(__file__).parent.parent / "models"
FEEDBACK_FILE = MODELS_DIR / "feedback.json"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
PUBMED_SEARCH_API    = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_API     = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ARXIV_API            = "https://export.arxiv.org/api/query"

MEDICAL_KEYWORDS = {
    "disease","cancer","drug","clinical","patient","medical","health",
    "hospital","diagnosis","therapy","treatment","covid","virus",
    "infection","surgery","cardiac","heart","brain","tumor","diabetes",
    "vaccine","gene","protein","biological","medicine","pharmaceutical",
    "epidemic","syndrome","obesity","stroke","alzheimer","parkinson",
    "depression","anxiety","mental","neurology","pathology","radiology",
}

class RecommendationEngine:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None
        self.is_loaded = False
        self.total_papers = "live (Semantic Scholar + PubMed + arXiv)"
        self.feedback: Dict[str, int] = {}
        self._load_feedback()

    def load(self):
        print("[1/1] Loading SentenceTransformer model...")
        self.model = SentenceTransformer(self.model_name)
        self.is_loaded = True
        print("Engine ready.")

    def _is_medical(self, query: str) -> bool:
        return bool(set(query.lower().split()) & MEDICAL_KEYWORDS)

    # ── Semantic Scholar ─────────────────────────────────────────────
    def _fetch_semantic_scholar(self, query: str, max_results: int = 100) -> List[dict]:
        params = urllib.parse.urlencode({
            "query": query,
            "limit": min(max_results, 100),
            "fields": "paperId,title,abstract,authors,year,externalIds,publicationTypes"
        })
        url = f"{SEMANTIC_SCHOLAR_API}?{params}"
        headers = {"User-Agent": "ResearchLens/1.0"}
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        if api_key:
            headers["x-api-key"] = api_key

        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as r:
                    data = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = 2 ** attempt
                    print(f"SS rate limit, waiting {wait}s...")
                    time.sleep(wait)
                    if attempt == 2:
                        print("SS unavailable, using fallback.")
                        return []
                else:
                    print(f"SS HTTP error: {e.code}")
                    return []
            except Exception as e:
                print(f"SS error: {e}")
                return []

        papers = []
        for p in data.get("data", []):
            if not p.get("title"):
                continue
            authors = ", ".join(a.get("name", "") for a in p.get("authors", [])[:5])
            arxiv_id = (p.get("externalIds") or {}).get("ArXiv", "")
            pid = arxiv_id if arxiv_id else p.get("paperId", "")
            papers.append({
                "id": pid,
                "title": p.get("title", ""),
                "abstract": p.get("abstract") or "No abstract available.",
                "authors": authors,
                "categories": ", ".join(p.get("publicationTypes") or []),
                "year": str(p.get("year") or ""),
                "source": "arxiv" if arxiv_id else "semantic_scholar",
            })
        print(f"Semantic Scholar: {len(papers)} papers")
        return papers

    # ── arXiv (fallback) ─────────────────────────────────────────────
    def _fetch_arxiv(self, query: str, max_results: int = 80) -> List[dict]:
        short_query = " ".join(query.split()[:4])
        params = urllib.parse.urlencode({
            "search_query": f"all:{short_query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        })
        url = f"{ARXIV_API}?{params}"
        try:
            with urllib.request.urlopen(url, timeout=15, context=ssl_ctx) as r:
                data = r.read().decode("utf-8")
        except Exception as e:
            print(f"arXiv error: {e}")
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(data)
        papers = []
        for entry in root.findall("atom:entry", ns):
            try:
                pid = entry.find("atom:id", ns).text.strip().split("/abs/")[-1]
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                published = entry.find("atom:published", ns).text.strip()
                year = published[:4]
                authors = ", ".join(
                    a.find("atom:name", ns).text
                    for a in entry.findall("atom:author", ns)[:5]
                )
                cats = " ".join(c.get("term", "") for c in entry.findall("atom:category", ns))
                papers.append({
                    "id": pid, "title": title, "abstract": abstract,
                    "authors": authors, "categories": cats,
                    "year": year, "source": "arxiv",
                })
            except Exception:
                continue
        print(f"arXiv: {len(papers)} papers")
        return papers

    # ── PubMed ───────────────────────────────────────────────────────
    def _fetch_pubmed(self, query: str, max_results: int = 50) -> List[dict]:
        search_params = urllib.parse.urlencode({
            "db": "pubmed", "term": query,
            "retmax": max_results, "retmode": "json", "sort": "relevance"
        })
        try:
            with urllib.request.urlopen(
                f"{PUBMED_SEARCH_API}?{search_params}", timeout=10, context=ssl_ctx
            ) as r:
                ids = json.loads(r.read())["esearchresult"]["idlist"]
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

        if not ids:
            return []

        fetch_params = urllib.parse.urlencode({
            "db": "pubmed", "id": ",".join(ids),
            "rettype": "abstract", "retmode": "xml"
        })
        try:
            with urllib.request.urlopen(
                f"{PUBMED_FETCH_API}?{fetch_params}", timeout=15, context=ssl_ctx
            ) as r:
                xml_data = r.read()
        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []

        papers = []
        try:
            root = ET.fromstring(xml_data)
            for article in root.findall(".//PubmedArticle"):
                try:
                    pmid  = article.findtext(".//PMID", "")
                    title = article.findtext(".//ArticleTitle", "No title")
                    abstract = " ".join(
                        a.text or "" for a in article.findall(".//AbstractText")
                    ) or "No abstract available."
                    year    = article.findtext(".//PubDate/Year", "")
                    authors = ", ".join(
                        f"{a.findtext('ForeName','')} {a.findtext('LastName','')}".strip()
                        for a in article.findall(".//Author")[:5]
                    )
                    mesh = [m.findtext("DescriptorName","") for m in article.findall(".//MeshHeading")]
                    categories = ", ".join(filter(None, mesh[:4]))
                    papers.append({
                        "id": f"pubmed-{pmid}", "title": title,
                        "abstract": abstract[:800], "authors": authors,
                        "categories": categories, "year": year, "source": "pubmed",
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"PubMed XML error: {e}")
        print(f"PubMed: {len(papers)} papers")
        return papers

    # ── Main recommend ───────────────────────────────────────────────
    def recommend(self, query: str, top_n: int = 10, domain_filter: Optional[str] = None) -> List[dict]:
        is_medical = self._is_medical(query)

        # 1. Try Semantic Scholar first
        ss_papers = self._fetch_semantic_scholar(query, max_results=50)

        # 2. If SS returned nothing (rate limited), fall back to arXiv
        if not ss_papers:
            print("Falling back to arXiv...")
            ss_papers = self._fetch_arxiv(query, max_results=50)

        # 3. PubMed for medical queries always
        pubmed_papers = self._fetch_pubmed(query, max_results=30) if is_medical else []

        # 4. Merge & deduplicate
        seen, papers = set(), []
        for p in ss_papers + pubmed_papers:
            t = p["title"].lower().strip()
            if t and t not in seen:
                seen.add(t)
                papers.append(p)

        print(f"Total unique papers: {len(papers)}")
        if not papers:
            return []

        if domain_filter:
            papers = [p for p in papers if domain_filter.lower() in p["categories"].lower()]
        if not papers:
            return []

        # 5. Encode title + abstract for semantic ranking
        query_emb = self.model.encode([query], normalize_embeddings=True)
        texts = [p['title'] for p in papers]
        embs  = self.model.encode(texts, normalize_embeddings=True, batch_size=128)
        scores = cosine_similarity(query_emb, embs)[0]

        ranked = sorted(zip(scores, papers), key=lambda x: x[0], reverse=True)

        results = []
        for score, paper in ranked[:top_n]:
            pid = paper["id"]
            if paper["source"] == "arxiv":
                clean = pid.replace("abs-","").split("v")[0]
                pdf_url = f"https://arxiv.org/pdf/{clean}"
            elif paper["source"] == "pubmed":
                pmid = pid.replace('pubmed-', '')
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/search/?query={pmid}"
            results.append({
                "id": pid,
                "title": paper["title"],
                "abstract": paper["abstract"][:600] + ("..." if len(paper["abstract"]) > 600 else ""),
                "authors": paper["authors"],
                "categories": paper["categories"],
                "match_score": round(float(score) * 100, 2),
                "year": paper["year"],
                "pdf_url": pdf_url,
                "source": paper["source"],
            })
        return results

    def get_domains(self) -> List[str]:
        return [
        # Computer Science
        "cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE", "cs.RO", "cs.IR",
        # Statistics & Math
        "stat.ML", "math.OC",
        # Physics & Quantum
        "quant-ph", "physics",
        # Biology & Medicines
        "q-bio", "q-bio.QM",
        # Engineering
        "eess.IV", "eess.SP",
        # Economics
        "econ.EM",
        # Publication Types
        "Review", "JournalArticle", "Conference",]
    def record_feedback(self, paper_id: str, relevant: bool):
        self.feedback[paper_id] = 1 if relevant else 0
        self._save_feedback()

    def _load_feedback(self):
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                self.feedback = json.load(f)

    def _save_feedback(self):
        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(self.feedback, f, indent=2)