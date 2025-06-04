from typing import List

class HybridRetriever:
    def retrieve(self, query: str) -> List[str]:
        # TODO: implement retrieval logic
        return []

class PromptBuilder:
    def build(self, question: str, docs: List[str]) -> str:
        return f"Question: {question}\n" + "\n".join(docs)

class AnswerGenerator:
    def generate(self, question: str, docs: List[str]) -> str:
        prompt = PromptBuilder().build(question, docs)
        # TODO: call LLM with prompt
        return ""
