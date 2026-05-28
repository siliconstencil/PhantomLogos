import os
import re
import time
from typing import Any

from src.architrave.sovereign_middleware import (
    MiddlewareHook,
    MiddlewareRequest,
    MiddlewareResponse,
)
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

logger = setup_logger(__name__)


REPAIR_MODEL = os.getenv("LOCAL_REPAIR_MODEL", "qwen3.5-2b-ud:latest")
QUALITY_THRESHOLD = float(os.getenv("LOCAL_REPAIR_THRESHOLD", "0.6"))


class LocalRepairMiddleware(MiddlewareHook):
    def __init__(self, model: str = REPAIR_MODEL, threshold: float = QUALITY_THRESHOLD) -> None:
        self.model = model
        self.threshold = threshold

    async def after(self, req: MiddlewareRequest, resp: Any, log: list[dict]) -> Any:
        if not isinstance(resp, MiddlewareResponse):
            return resp

        t_hook = time.time()

        quality_score = await self._assess_quality(req, resp)
        log.append(
            {
                "hook": "LocalRepair",
                "action": "assess",
                "quality_score": quality_score,
                "threshold": self.threshold,
                "ts": time.time() - t_hook,
            }
        )

        if quality_score >= self.threshold:
            logger.info(f"LocalRepair: Quality OK ({quality_score:.2f} >= {self.threshold})")
            return resp

        logger.warning(
            f"LocalRepair: Quality LOW ({quality_score:.2f} < {self.threshold}). Attempting repair..."
        )
        repaired = await self._repair_response(req, resp)
        log.append(
            {
                "hook": "LocalRepair",
                "action": "repaired",
                "original_score": quality_score,
                "ts": time.time() - t_hook,
            }
        )

        if repaired:
            resp.text = repaired
            resp.thoughts = (resp.thoughts or "") + f"\n[REPAIRED by {self.model}]"

        return resp

    async def _assess_quality(self, req: MiddlewareRequest, resp: MiddlewareResponse) -> float:
        try:
            client = get_ollama_client()
            response = await client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a quality assessor. Rate the response on a scale of 0.0 to 1.0. "
                            "Consider: correctness, completeness, clarity, and relevance to the prompt. "
                            "Respond with ONLY a float number between 0.0 and 1.0."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Prompt: {req.prompt}\n\nResponse: {resp.text}\n\nQuality score:",
                    },
                ],
                options={"temperature": 0.0, "num_predict": 10},
            )
            raw = response.get("message", {}).get("content", "0.5").strip()
            match = re.search(r"0\.[0-9]+|1\.0+", raw)
            score = float(match.group()) if match else 0.5
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"LocalRepair: Quality assessment failed ({e})")
            return 1.0

    async def _repair_response(
        self, req: MiddlewareRequest, resp: MiddlewareResponse
    ) -> str | None:
        try:
            client = get_ollama_client()
            response = await client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a response repair specialist. The original response was low quality. "
                            "Rewrite it to be correct, complete, clear, and directly relevant to the user's prompt. "
                            "Keep the same length and format. Output ONLY the repaired response."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Original prompt: {req.prompt}\n\nLow quality response:\n{resp.text}\n\nRepaired response:",
                    },
                ],
                options={"temperature": 0.2, "num_predict": 2048},
            )
            return response.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"LocalRepair: Repair failed ({e})")
            return None
