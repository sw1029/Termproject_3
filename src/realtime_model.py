from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
from .retrieval.rag_pipeline import HybridRetriever, AnswerGenerator

app = FastAPI()
retriever = HybridRetriever()
generator = AnswerGenerator()

LOG_PATH = Path("outputs/realtime_output.json")

def append_log(record: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")

class Query(BaseModel):
    question: str

@app.post('/predict')
async def predict(query: Query):
    # Placeholder for LLM classifier
    return {'label': 0}

@app.post('/answer')
async def answer(query: Query):
    docs = retriever.retrieve(query.question)
    text = generator.generate(query.question, docs)
    append_log({"user": query.question, "model": text})
    return {'answer': text, 'sources': docs}
