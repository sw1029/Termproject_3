import json
from typing import List, Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from openai import OpenAI

from ..utils.config import settings


class HybridRetriever:
    def retrieve(self, query: str) -> List[str]:
        """Return list of documents matching the query (placeholder)."""
        return []


class PromptBuilder:
    """Build system prompt for the generator."""

    def build(self, question: str, docs: List[str]) -> str:
        context = "\n".join(docs) if docs else "참고할 정보가 없습니다."
        prompt = f"""
당신은 충남대학교 관련 정보를 안내하는 챗봇입니다.
주어진 '참고 자료'를 근거로 사용자의 질문에 명확하고 친절하게 답변해야 합니다.
참고 자료에 없는 내용은 답변에 포함하지 마세요.

[참고 자료]
{context}

[질문]
{question}

[답변]
"""
        return prompt.strip()


class AnswerGenerator:
    """Generate an answer using a local model or OpenAI API."""

    def __init__(self) -> None:
        self.model_type = settings.generator_model_type
        self.model = None
        self.tokenizer = None
        self.client = None

        if self.model_type == "local":
            model_name = settings.generator_model_name_or_path
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                torch_dtype=torch.bfloat16,
            )
            print(f"\u2705 Local Generator Model Loaded: {model_name}")
        elif self.model_type == "openai":
            if not settings.openai_api_key or settings.openai_api_key == "YOUR_API_KEY":
                raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
            self.client = OpenAI(api_key=settings.openai_api_key)
            print(f"\u2705 OpenAI Client Initialized for model: {settings.openai_model_name}")

    def generate(self, question: str, docs: List[Dict[str, Any]]) -> str:
        doc_texts = [json.dumps(d, ensure_ascii=False) for d in docs]
        prompt = PromptBuilder().build(question, doc_texts)

        if self.model_type == "local" and self.model and self.tokenizer:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=512)
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return answer.split("[답변]")[-1].strip()

        if self.model_type == "openai" and self.client:
            response = self.client.chat.completions.create(
                model=settings.openai_model_name,
                messages=[
                    {"role": "system", "content": "당신은 충남대학교 정보를 안내하는 챗봇입니다."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()

        return "답변 생성 모델이 올바르게 설정되지 않았습니다."
