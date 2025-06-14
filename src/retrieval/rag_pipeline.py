import json
from typing import List


class HybridRetriever:
    def retrieve(self, query: str) -> List[str]:
        """Return list of documents matching the query (placeholder)."""
        return []


class PromptBuilder:
    """Construct system prompt for RAG generation."""

    def build(self, question: str, docs: List[str]) -> str:
        context = "\n".join(docs) if docs else "참고할 정보가 없습니다."
        prompt = f"""
당신은 충남대학교 관련 정보를 안내하는 챗봇입니다.
주어진 '참고 자료'를 근거로 사용자의 질문에 답하세요.

[참고 자료]
{context}

[질문]
{question}

[답변]
"""
        return prompt.strip()


class AnswerGenerator:
    """Generate answer from question and context."""

    def __init__(self):
        self.model = None
        self.tokenizer = None

    def generate(self, question: str, docs: List[dict]) -> str:
        doc_texts = [json.dumps(d, ensure_ascii=False) for d in docs]
        prompt = PromptBuilder().build(question, doc_texts)
        if not self.model:
            first = doc_texts[0] if doc_texts else "없음"
            return f"RAG 파이프라인 결과 (모델 미구현)\n질문: {question}\n참고: {first}"
        # 실제 LLM 호출 로직은 여기에 구현
        return ""
