from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from recommender import RecommendationEngine

app = FastAPI(title="Research Paper Recommendation System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RecommendationEngine()

class QueryRequest(BaseModel):
    query: str
    top_n: int = 10
    domain_filter: Optional[str] = None

class FeedbackRequest(BaseModel):
    paper_id: str
    relevant: bool

class Paper(BaseModel):
    id: str
    title: str
    abstract: str
    authors: str
    categories: str
    match_score: float
    year: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    print("Loading recommendation engine...")
    engine.load()
    print("Engine ready.")

@app.get("/")
def root():
    return {"status": "ok", "message": "Research Paper Recommendation API"}

@app.get("/status")
def status():
    return {
        "loaded": engine.is_loaded,
        "total_papers": engine.total_papers,
        "model": engine.model_name
    }

@app.post("/recommend", response_model=List[Paper])
def recommend(req: QueryRequest):
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Engine not loaded yet.")
    results = engine.recommend(req.query, req.top_n, req.domain_filter)
    return results

@app.get("/domains")
def get_domains():
    return {"domains": engine.get_domains()}

@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    engine.record_feedback(req.paper_id, req.relevant)
    return {"status": "recorded"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
