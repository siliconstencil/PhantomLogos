from src.lachesis.verifiers.z3_engine import verify_logic
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class GraphVerifier:
    """[SRC:axis_11] Verifies LangGraph transitions using Z3 SMT solver."""

    def _build_red_zone_smt(self, overall_score: float, verification_retry: int) -> str:
        return f"""
        (declare-const overall_score Real)
        (declare-const verification_retry Int)
        (assert (= overall_score {overall_score}))
        (assert (= verification_retry {verification_retry}))
        (assert (or (< overall_score 0.4) (>= verification_retry 3)))
        """

    def _build_deadlock_resolver_smt(
        self, threshold: float, verification_retry: int, overall_score: float
    ) -> str:
        return f"""
        (declare-const threshold Real)
        (declare-const verification_retry Int)
        (declare-const overall_score Real)
        (assert (= threshold {threshold}))
        (assert (= verification_retry {verification_retry}))
        (assert (= overall_score {overall_score}))
        (assert (or (< overall_score 0.4) (>= verification_retry 3)))
        (assert (>= threshold 0.5))
        """

    def _build_deadlock_mutation_smt(
        self,
        threshold: float,
        old_threshold: float,
        retry: int,
        iteration: int,
        old_iteration: int,
        mem_sync: bool,
    ) -> str:
        mem_sync_str = "true" if mem_sync else "false"
        return f"""
        (declare-const threshold Real)
        (declare-const old_threshold Real)
        (declare-const retry Int)
        (declare-const iteration Int)
        (declare-const old_iteration Int)
        (declare-const mem_sync Bool)
        (assert (= old_threshold {old_threshold}))
        (assert (= threshold {threshold}))
        (assert (= retry {retry}))
        (assert (= iteration {iteration}))
        (assert (= old_iteration {old_iteration}))
        (assert (= mem_sync {mem_sync_str}))
        (assert (= retry 0))
        (assert (= iteration (+ old_iteration 1)))
        (assert (= mem_sync true))
        (assert (= threshold (ite (> (- old_threshold 0.1) 0.5) (- old_threshold 0.1) 0.5)))
        """

    def _build_deadlock_error_smt(
        self,
        threshold: float,
        old_threshold: float,
        retry: int,
        old_retry: int,
        iteration: int,
        old_iteration: int,
        mem_sync: bool,
    ) -> str:
        mem_sync_str = "true" if mem_sync else "false"
        return f"""
        (declare-const threshold Real)
        (declare-const old_threshold Real)
        (declare-const retry Int)
        (declare-const old_retry Int)
        (declare-const iteration Int)
        (declare-const old_iteration Int)
        (declare-const mem_sync Bool)
        (assert (= old_threshold {old_threshold}))
        (assert (= threshold {threshold}))
        (assert (= old_retry {old_retry}))
        (assert (= retry {retry}))
        (assert (= iteration {iteration}))
        (assert (= old_iteration {old_iteration}))
        (assert (= mem_sync {mem_sync_str}))
        (assert (= mem_sync false))
        (assert (= retry old_retry))
        (assert (= threshold old_threshold))
        (assert (= iteration old_iteration))
        """

    async def verify_red_zone_gate(self, overall_score: float, verification_retry: int) -> dict:
        """Verifies if the red zone gate transition should trigger (overall_score < 0.4 or retry >= 3)."""
        smt = self._build_red_zone_smt(overall_score, verification_retry)
        return await verify_logic(smt)

    async def verify_deadlock_resolver(
        self, threshold: float, verification_retry: int, overall_score: float = 0.5
    ) -> dict:
        """Verifies if the deadlock resolver safety precondition (threshold >= 0.5) is satisfied under red zone trigger."""
        smt = self._build_deadlock_resolver_smt(threshold, verification_retry, overall_score)
        return await verify_logic(smt)

    async def verify_deadlock_mutation(
        self,
        threshold: float,
        old_threshold: float,
        retry: int,
        iteration: int,
        old_iteration: int,
        mem_sync: bool,
    ) -> dict:
        """Verifies if the deadlock resolver mutation invariants (post-conditions) are correctly satisfied."""
        smt = self._build_deadlock_mutation_smt(
            threshold, old_threshold, retry, iteration, old_iteration, mem_sync
        )
        return await verify_logic(smt)

    async def verify_deadlock_error(
        self,
        threshold: float,
        old_threshold: float,
        retry: int,
        old_retry: int,
        iteration: int,
        old_iteration: int,
        mem_sync: bool,
    ) -> dict:
        """Verifies if the deadlock resolver error path invariants (no mutation, memory_sync=False) are correctly satisfied."""
        smt = self._build_deadlock_error_smt(
            threshold, old_threshold, retry, old_retry, iteration, old_iteration, mem_sync
        )
        return await verify_logic(smt)

    async def run_all(self, state: dict, old_state: dict) -> dict:
        """Runs all relevant transition verifications based on active state."""
        results = {}

        overall_score = state.get("overall_score", 1.0)
        verification_retry = state.get("verification_retry", 0)
        results["red_zone"] = await self.verify_red_zone_gate(overall_score, verification_retry)

        threshold = state.get("threshold", 0.7)
        results["deadlock_pre"] = await self.verify_deadlock_resolver(
            threshold, verification_retry, overall_score
        )

        old_threshold = old_state.get("threshold", 0.7)
        retry = state.get("verification_retry", 0)
        old_retry = old_state.get("verification_retry", 0)
        iteration = state.get("iteration", 0)
        old_iteration = old_state.get("iteration", 0)
        mem_sync = state.get("memory_sync", True)

        if mem_sync:
            results["deadlock_mutation"] = await self.verify_deadlock_mutation(
                threshold, old_threshold, retry, iteration, old_iteration, mem_sync
            )
        else:
            results["deadlock_error"] = await self.verify_deadlock_error(
                threshold, old_threshold, retry, old_retry, iteration, old_iteration, mem_sync
            )

        return results
