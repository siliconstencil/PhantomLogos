import asyncio
import json

from src.lachesis import get_output_guard
from src.utils.logging_config import setup_logger

from ..eidos import CritiqueResult
from ..gnosis import get_dynamic_context
from ..hephaestus import get_meta, get_sophia_instructions
from ._gateway import get_gateway

logger = setup_logger(__name__)

_session_cache_map: dict[str, str] = {}


async def run_refine(
    task: str, draft: str, critique: CritiqueResult, session_id: str = "default"
) -> str:
    logger.info(f"Sophia: Refining Solution in session {session_id}...")
    stable, dynamic, block_signal = await get_dynamic_context(
        "sophia", task_hint=task, session_id=session_id
    )
    architrave = get_gateway()
    fallback_model = block_signal.get("fallback_model")

    critique_str = (
        json.dumps(critique)
        if isinstance(critique, dict)
        else (critique.model_dump_json() if hasattr(critique, "model_dump_json") else str(critique))
    )
    inst = get_sophia_instructions([])
    prompt = (
        f"Task: {task}\nDraft: {draft}\nCritique: {critique_str}\n\nDYNAMIC CONTEXT:\n{dynamic}"
    )
    try:
        sys_instruction = f"You are the Master Refiner.\n\nSTABLE CONTEXT:\n{stable}\n\n{inst['timestamp']}\n\n{inst['citation']}\n\nProduce the final version, ensuring all claims are cited with [SRC:axis_N]."
        if fallback_model:
            logger.warning(
                f"Sophia: Token budget exceeded in refine. Routing to local fallback model: {fallback_model}"
            )
            response = await architrave._local_fallback(
                prompt=prompt,
                system_instruction=sys_instruction,
                thoughts="Token budget fallback route in refine.",
                model=fallback_model,
            )
        else:
            generate_kwargs = dict(
                prompt=prompt,
                system_instruction=sys_instruction,
                thinking=True,
                session_id=session_id,
            )
            response = await asyncio.wait_for(
                architrave.generate_async(**generate_kwargs),
                timeout=60.0,
            )
        result_text = response.text
    except TimeoutError:
        logger.error("Sophia: Refine timed out after 60s")
        return draft
    except Exception as e:
        logger.error(f"Sophia: Refine failed ({e})", exc_info=True)
        return draft

    guard = get_output_guard()
    check = guard.check(
        result_text,
        agent_id="sophia",
        context={"function": "run_refine", "require_timestamp": True, "session_id": session_id},
    )
    _delta = check["score_delta"] if check["violations"] else 1.0
    get_meta().adjust_reliability(
        agent_id="sophia",
        delta=_delta,
        violation_type=check["violations"][0] if check["violations"] else "",
        session_id=session_id,
    )

    if check["violations"] and check["action"] == "reject":
        logger.warning(f"Guardrail rejected refine output ({check['violations']}). Retrying.")
        try:
            sys_instruction_retry = f"You are the Master Refiner.\n\nSTABLE CONTEXT:\n{stable}\n\n{inst['timestamp']}\n\nProduce the final version."
            if fallback_model:
                retry_response = await architrave._local_fallback(
                    prompt=prompt,
                    system_instruction=sys_instruction_retry,
                    thoughts="Token budget fallback route in refine retry.",
                    model=fallback_model,
                )
            else:
                retry_kwargs = dict(
                    prompt=prompt,
                    system_instruction=sys_instruction_retry,
                    thinking=True,
                    session_id=session_id,
                )
                retry_response = await asyncio.wait_for(
                    architrave.generate_async(**retry_kwargs),
                    timeout=60.0,
                )
            result_text = retry_response.text
        except (TimeoutError, Exception):
            logger.error("Sophia: Refine retry also failed")
            return draft

    return result_text
