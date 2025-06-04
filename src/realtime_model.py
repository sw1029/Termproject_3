from fastapi import FastAPI
from pydantic import BaseModel
from .retrieval.rag_pipeline import HybridRetriever, AnswerGenerator

app = FastAPI()
retriever = HybridRetriever()
generator = AnswerGenerator()

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
    return {'answer': text, 'sources': docs}
