from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
from .retrieval.rag_pipeline import HybridRetriever, AnswerGenerator
from .answers import (
    academic_calendar_answer,
    shuttle_bus_answer,
    graduation_req_answer,
    meals_answer,
    notices_answer,
)


class SimpleClassifier:
    """Very naive rule based classifier returning label 0-4."""

    KEYWORDS = {
        0: ["졸업", "졸업요건", "졸업 요건"],
        1: ["공지", "notice"],
        2: ["학사일정", "academic", "캘린더"],
        3: ["식단", "학식", "메뉴"],
        4: ["셔틀", "버스", "통학"],
    }

    def predict(self, text: str) -> int:
        text = text.lower()
        for label, words in self.KEYWORDS.items():
            for w in words:
                if w.lower() in text:
                    return label
        return 1

app = FastAPI()
retriever = HybridRetriever()
generator = AnswerGenerator()
classifier = SimpleClassifier()

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
    label = classifier.predict(query.question)
    return {'label': label}

def _route_answer(label: int, question: str) -> str:
    if label == 0:
        return graduation_req_answer.generate_answer(question)
    if label == 1:
        return notices_answer.generate_answer(question)
    if label == 2:
        return academic_calendar_answer.generate_answer(question)
    if label == 3:
        return meals_answer.generate_answer(question)
    if label == 4:
        return shuttle_bus_answer.generate_answer(question)
    docs = retriever.retrieve(question)
    return generator.generate(question, docs)


@app.post('/answer')
async def answer(query: Query):
    label = classifier.predict(query.question)
    text = _route_answer(label, query.question)
    append_log({"user": query.question, "model": text, "label": label})
    return {'answer': text, 'label': label}
