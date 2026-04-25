# ResearchLens — Research Paper Recommendation System
**BIS586 Mini Project | Dept. of ISE, GSSSIETW, Mysuru**

---

## Stack
| Layer | Tech |
|---|---|
| Backend | FastAPI + Python 3.10+ |
| ML Model | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Vector Search | FAISS (CPU) |
| Frontend | React + Vite + TailwindCSS |

---

## Project Structure
```
research-recommender/
├── backend/
│   ├── main.py          ← FastAPI app
│   ├── recommender.py   ← ML engine (embeddings + FAISS)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/   ← Header, PaperCard
│   │   └── pages/        ← SearchPage, ResultsPage
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── data/                 ← PUT YOUR DATASET HERE
│   └── (arxiv-metadata-oai-snapshot.json  OR  arxiv_data.csv)
└── models/               ← Auto-created on first run
    └── (embeddings.npy, feedback.json)
```

---

## Step-by-Step Setup

### Step 1 — Put Your Dataset in /data
Copy your downloaded arXiv dataset into the `data/` folder.
Supported filenames (in priority order):
- `arxiv_data.parquet`  ← fastest if you have it
- `arxiv_data.csv`
- `arxiv-metadata-oai-snapshot.json`  ← raw arXiv dump

### Step 2 — Backend Setup
Open a terminal and run:
```bash
cd research-recommender/backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 3 — Start the Backend
```bash
# Still inside backend/ with venv active
python main.py
```

**First run:** The server will download the SentenceTransformer model (~90MB) and build embeddings for all papers. This can take **10–30 minutes** depending on dataset size. After that, embeddings are cached in `models/embeddings.npy` — subsequent starts take ~30 seconds.

You'll see:
```
[1/4] Loading SentenceTransformer model...
[2/4] Loading dataset...
  Loaded 200,000 papers.
[3/4] Building embeddings (first run)...
[4/4] Building FAISS index...
Engine ready.
```

Then visit http://localhost:8000/status to verify.

### Step 4 — Frontend Setup
Open a **new terminal** (keep backend running):
```bash
cd research-recommender/frontend
npm install
npm run dev
```

Visit **http://localhost:5173** in your browser.

---

## How It Works (for your viva)
1. **User types a query** (keywords or abstract snippet)
2. Backend encodes query using `all-MiniLM-L6-v2` → 384-dim vector
3. **FAISS IndexFlatIP** does inner-product search (≡ cosine on normalized vectors) across all paper embeddings
4. Top-N papers returned with **% match score** = cosine similarity × 100
5. User can mark papers as relevant/not relevant → stored in `feedback.json`

---

## Troubleshooting
| Problem | Fix |
|---|---|
| `FileNotFoundError: No dataset found` | Make sure your dataset is inside the `data/` folder with correct filename |
| Backend hangs on "Building embeddings" | Normal on first run — wait for completion |
| Frontend shows "Backend not reachable" | Make sure backend is running on port 8000 |
| FAISS install fails on Windows | Run `pip install faiss-cpu` separately |
| Out of memory | Open `recommender.py` and lower `200_000` to `100_000` |
