from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from .retrieval.rag_pipeline import HybridRetriever, AnswerGenerator
from .utils.config import settings
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
            return_all_scores=True,
        )

    def predict(self, text: str) -> int:
        result = self.pipe(text)[0]
        best = max(result, key=lambda x: x["score"])
        return int(best["label"].split("_")[-1])

app = FastAPI()

# Initialize core pipeline components once at startup
retriever = HybridRetriever()
generator = AnswerGenerator()
classifier = LLMClassifier()

# Map labels to answer generator functions
ANSWER_HANDLERS = {
    0: graduation_req_answer.generate_answer,
    1: notices_answer.generate_answer,
    2: academic_calendar_answer.generate_answer,
    3: meals_answer.generate_answer,
    4: shuttle_bus_answer.generate_answer,
}

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
    """Route question to the appropriate answer handler."""

    handler = ANSWER_HANDLERS.get(label)
    if handler:
        return handler(question)

    docs = retriever.retrieve(question)
    context = [{"text": d} for d in docs]
    return "".join(list(generator.generate(question, context)))


@app.post('/answer')
async def answer(query: Query):
    """Return an answer for ``query`` with detailed error handling."""
    label = -1
    try:
        # Step 1: classify the question
        label = classifier.predict(query.question)

        # Step 2: generate answer based on the label
        response_text = _route_answer(label, query.question)

        append_log({"user": query.question, "model": response_text, "label": label, "status": "SUCCESS"})
        return {"answer": response_text}

    except Exception as e:
        error_code = "ERR_UNKNOWN"
        error_message = f"알 수 없는 오류가 발생했습니다: {e}"
        if label == -1:
            error_code = "ERR_CLASSIFY"
            error_message = f"질문 분류 중 오류가 발생했습니다: {e}"
        else:
            error_code = f"ERR_ANSWER_{label}"
            error_message = f"답변 생성 중 오류가 발생했습니다 (Label: {label}): {e}"

        # Log failure
        append_log({"user": query.question, "model": error_message, "label": label, "status": "FAIL"})

        raise HTTPException(status_code=500, detail={"code": error_code, "message": error_message})
