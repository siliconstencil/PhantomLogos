import ollama
import json
import re
from typing import Tuple
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

ROUTER_MODEL = "functiongemma-270m:latest"

TASK_CATEGORIES = {
    "code": "1",
    "math": "2",
    "reasoning": "3",
    "retrieval": "4",
    "chat": "5",
    "vision": "6",
}

CATEGORY_PROMPTS = {
    "code": "You are a Code Specialist. Provide a clean, working code solution.",
    "math": "You are a Math Specialist. Verify with symbolic reasoning before answering.",
    "reasoning": "You are a Reasoning Specialist. Think step by step and verify logic.",
    "retrieval": "You are a Knowledge Specialist. Use available context to answer accurately.",
    "chat": "You are a Conversational Agent. Provide a helpful, concise response.",
    "vision": "You are a Vision Analyst. Analyze the image and provide a detailed response.",
}


class TaskRouter:
    """
    FunctionGemma-based task classifier.
    Routes incoming tasks to the appropriate specialist agent.
    """
    def __init__(self, model: str = ROUTER_MODEL):
        self.model = model

    def classify(self, task: str) -> str:
        prompt = (
            "You are a task classifier. Respond in JSON format.\n"
            "Format: {\"category\": \"string\", \"confidence\": float}\n"
            "Categories: code, math, reasoning, retrieval, chat, vision.\n\n"
            f"Task: {task}"
        )
        try:
            resp = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.0, "num_predict": 30},
            )
            data = json.loads(resp["message"]["content"])
            category = data.get("category", "chat").lower()
            confidence = data.get("confidence", 1.0)

            # Sprint F: Confidence Guard (0.7 Threshold)
            if confidence >= 0.7:
                for cat in TASK_CATEGORIES:
                    if cat in category:
                        return cat
            
            logger.warning(f"Router: Low confidence ({confidence}) for category '{category}'. Falling back to keywords.")
            return self._keyword_fallback(task)

        except Exception as e:
            logger.error(f"Router: Model classification failed ({e}). Falling back to keywords.")
            return self._keyword_fallback(task)

    def _keyword_fallback(self, task: str) -> str:
        t_low = task.lower()
        if any(kw in t_low for kw in ["image", "picture", "screenshot", "photo", "diagram", "ocr", "visual", "screen"]):
            return "vision"
        if any(kw in t_low for kw in ["code", "function", "class", "def ", "python", "javascript", "script"]):
            return "code"
        if any(kw in t_low for kw in ["calculate", "math", "algebra", "equation", "formula"]):
            return "math"
        if any(kw in t_low for kw in ["explain", "why", "how", "analyze", "compare", "reason"]):
            return "reasoning"
        if any(kw in t_low for kw in ["search", "find", "document", "info", "context"]):
            return "retrieval"
        return "chat"

    def route(self, task: str) -> Tuple[str, str]:
        category = self.classify(task)
        system_prompt = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["chat"])
        return category, system_prompt
