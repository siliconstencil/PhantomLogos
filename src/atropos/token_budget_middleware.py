from src.architrave.sovereign_middleware import (
    MiddlewareHook,
    MiddlewareRequest,
)
from src.atropos.token_budget import get_token_guard
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class TokenBudgetMiddleware(MiddlewareHook):
    def __init__(self, daily_limit: int = 500000, hourly_limit: int = 80000) -> None:
        self.guard = get_token_guard(daily_limit=daily_limit)
        self.guard.daily_limit = daily_limit
        self.guard.hourly_limit = hourly_limit
        self._hourly_limit = hourly_limit
        self.guard.hourly_limit = hourly_limit
        self._hourly_limit = hourly_limit

    async def before(self, req: MiddlewareRequest, _log: list[dict]) -> MiddlewareRequest | None:
        prompt_tokens = self._estimate_tokens(req.prompt)
        sys_tokens = self._estimate_tokens(req.system_instruction or "")

        daily_remaining = self.guard.remaining_daily()
        hourly_remaining = self.guard.remaining_hourly()

        _log.append(
            {
                "hook": "TokenBudget",
                "action": "check",
                "prompt_tokens": prompt_tokens,
                "sys_tokens": sys_tokens,
                "total_estimate": prompt_tokens + sys_tokens,
                "daily_remaining": daily_remaining,
                "hourly_remaining": hourly_remaining,
            }
        )

        if prompt_tokens + sys_tokens > daily_remaining:
            logger.error(
                f"TokenBudget: CRITICAL - Daily limit exceeded (need {prompt_tokens + sys_tokens}, remaining {daily_remaining})"
            )
            _log.append(
                {"hook": "TokenBudget", "action": "blocked", "reason": "daily_limit_exceeded"}
            )
            return None

        if prompt_tokens + sys_tokens > hourly_remaining:
            logger.warning(
                f"TokenBudget: Hourly limit exceeded (need {prompt_tokens + sys_tokens}, remaining {hourly_remaining})"
            )
            _log.append(
                {"hook": "TokenBudget", "action": "blocked", "reason": "hourly_limit_exceeded"}
            )
            if self.guard._hourly_used + prompt_tokens + sys_tokens > self._hourly_limit * 2:
                try:
                    from cognition.sophia.hephaestus import _get_meta

                    _get_meta().adjust_reliability("sophia", -0.1, "token_budget_exceeded")
                except Exception as exc:
                    logger.warning("Reliability update failed: %s", exc)
            return None

        success = self.guard.consume(prompt_tokens + sys_tokens)
        if not success:
            _log.append({"hook": "TokenBudget", "action": "blocked", "reason": "consume_failed"})
            return None

        _log.append(
            {"hook": "TokenBudget", "action": "allowed", "consumed": prompt_tokens + sys_tokens}
        )
        return req

    def _estimate_tokens(self, text: str) -> int:
        try:
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return len(text) // 4
