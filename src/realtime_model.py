from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
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


class LLMClassifier:
    """Load fine-tuned sequence classification model to predict labels."""

    def __init__(self, model_path: str = "./models/classifier"):
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=device,
            return_all_scores=True,
        )

    def predict(self, text: str) -> int:
        result = self.pipe(text)[0]
        best = max(result, key=lambda x: x["score"])
        return int(best["label"].split("_")[-1])

app = FastAPI()
retriever = HybridRetriever()
generator = AnswerGenerator()
classifier = LLMClassifier()

LOG_PATH = Path("outputs/realtime_output.json")

def append_log(record: dict):
    """Append a record to ``realtime_output.json`` using a JSON array format."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = []
    if LOG_PATH.exists():
        text = LOG_PATH.read_text(encoding="utf-8").strip()
        if text:
            try:
                data = json.loads(text)
                records = data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                records = [json.loads(line) for line in text.splitlines() if line.strip()]
    records.append(record)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

class Query(BaseModel):
    question: str

@app.post('/predict')
async def predict(query: Query):
    label = classifier.predict(query.question)
    return {'label': label}

def _route_answer(label: int, question: str) -> str:
    context = []
    if label == 0:
        df = graduation_req_answer.get_context(question)
        if hasattr(df, 'to_dict'):
            context = df.to_dict('records')
        else:
            context = df
    elif label == 1:
        context = notices_answer.get_context(question)
    elif label == 2:
        context = academic_calendar_answer.get_context(question)
    elif label == 3:
        context = meals_answer.get_context(question)
    elif label == 4:
        context = shuttle_bus_answer.get_context(question)

    if not context:
        docs = retriever.retrieve(question)
        context = [{"text": d} for d in docs]

    return generator.generate(question, context)


@app.post('/answer')
async def answer(query: Query):
    label = classifier.predict(query.question)
    text = _route_answer(label, query.question)
    append_log({"user": query.question, "model": text, "label": label})
    return {'answer': text, 'label': label}
