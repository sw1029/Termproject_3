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
            device=device,
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

def _route_answer(label: int, question: str) -> StreamingResponse:
    """Route question to the appropriate answer module and stream the answer."""

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
        # ``HybridRetriever`` is expected to return a list of texts
        context = [{"text": d} for d in docs]

    return StreamingResponse(
        generator.generate(question, context), media_type="text/plain"
    )


@app.post('/answer')
async def answer(query: Query):
    """Return an answer for ``query`` with detailed error handling."""
    label = -1
    try:
        # Step 1: classify the question
        label = classifier.predict(query.question)

        # Step 2: generate answer based on the label
        response = _route_answer(label, query.question)

        # Log success (streaming content is not captured here)
        append_log({"user": query.question, "model": "[streaming]", "label": label, "status": "SUCCESS"})
        return response

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
