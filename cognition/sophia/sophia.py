import asyncio
import json
import os
import time

import yaml

from src.architrave import GatewayArchitrave
from src.lachesis import get_output_guard
from src.utils.logging_config import setup_logger
from src.utils.ollama_utils import get_ollama_client

from .gnosis import get_dynamic_context
from .eidos import CritiqueResult, ReasoningState, SophiaOutput
from .hephaestus import (
    _get_episodic,
    _get_meta,
    _get_monitor,
    _get_procedural,
    extract_first_json_block,
    get_sophia_instructions,
    strip_thinking_block,
)

logger = setup_logger(__name__)

_gateway_instance = None
_consecutive_draft_timeouts = 0


def _get_gateway():
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = GatewayArchitrave()
    return _gateway_instance


# --- Node Logic with Monitoring & Thinking Mode ---


@_get_monitor().trace("sophia")
async def run_draft(state: ReasoningState, thinking: bool = True) -> str | tuple:
    global _consecutive_draft_timeouts
    logger.info(f"Sophia: Generating Draft (Thinking Mode: {thinking})...")
    stable, dynamic, block_signal = await get_dynamic_context(
        "sophia", task_hint=state.task, session_id=state.session_id
    )

    if block_signal["block"]:
        # S3.2: L0 Force Override (bypass_memory_gate)
        if hasattr(state, "flags") and state.flags.get("bypass_memory_gate"):
            logger.info("Sophia: Hard Gate bypassed via L0 Force Override")
        else:
            logger.warning(f"Sophia: Hard Gate Triggered - {block_signal['reason']}")
            # Re-route to L0 alert via return (Wait for user override or retry with different model)
            return (
                f"HARD GATE: Task blocked due to previous failures. Reason: {block_signal['reason']}",
                [],
            )

    # Load tool whitelist and instructions
    try:
        with open(os.path.join("agent", "sophia.yaml")) as f:
            cfg = yaml.safe_load(f)
        tools = cfg.get("tools", [])
        skills_list = cfg.get("skills", [])
    except Exception:
        tools = ["ls", "semantic", "mapper", "vram", "report"]
        skills_list = []

    # Skill Injection (Phase 11.20.1)
    skill_context = ""
    if skills_list:
        from src.clotho.skill_loader import get_skill_loader

        loader = get_skill_loader()
        summaries = []
        for sname in skills_list:
            summary = loader.get_skill_summary(sname)
            if summary:
                summaries.append(summary)
        if summaries:
            skill_context = "ACTIVE SKILLS:\n" + "\n".join([str(s) for s in summaries if s])
            logger.info(f"Sophia: Injected {len(summaries)} skill summaries into draft context.")

    inst = get_sophia_instructions(tools)
    architrave = _get_gateway()

    try:
        response = await asyncio.wait_for(
            architrave.generate_async(
                prompt=f"DYNAMIC CONTEXT:\n{dynamic}\n\nTASK:\n{state.task}\n\nFAILURE AWARENESS MANDATE (Axis 8):\nReview Axis 8 in the dynamic context above. You MUST NOT repeat previous failure patterns.",
                system_instruction=f"You are the Sovereign Architect (Sophia) of Phantom Logos.\n\nSTABLE CONTEXT (GOVERNANCE):\n{stable}\n\n{skill_context}\n\n{inst['timestamp']}\n\n{inst['tool']}\n\n{inst['citation']}\n\nProvide a high-performance solution based on the 14-axis memory state.",
                thinking=thinking,
            ),
            timeout=60.0,
        )

        output = response.text
        # Clean thinking blocks for parsing
        clean_text = strip_thinking_block(output)

        # Phase 11.22.1: System Guard Error Handling
        if output.startswith("[SYSTEM GUARD]"):
            logger.warning("Sophia: System Guard message detected. Bypassing JSON parse.")
            return output, []

        # 1. Structured Parsing (Phase 11.18.4) - STRICT MODE
        parsed = None
        try:
            brace_depth = 0
            json_start = -1
            for i, ch in enumerate(clean_text):
                if ch == "{":
                    if brace_depth == 0:
                        json_start = i
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth == 0 and json_start >= 0:
                        json_str = clean_text[json_start : i + 1]
                        parsed = SophiaOutput.model_validate_json(json_str)
                        break
            if parsed is None:
                logger.error("Sophia: Model failed to provide structured JSON. REJECTING.")
                return "", []

            tool_calls = parsed.tool_calls
            logger.info(
                f"Sophia: Parsed structured output with {len(tool_calls)} tool calls and {len(parsed.technical_claims)} claims"
            )
        except Exception as pe:
            logger.error(f"Sophia: Schema validation failed ({pe}). Output: {clean_text[:100]}...")
            return "", []

        if tool_calls:
            if parsed and parsed.technical_claims:
                for call in tool_calls:
                    if call.get("tool") in ("vision", "vram"):
                        call["_claims"] = [c.model_dump() for c in parsed.technical_claims]

        guard = get_output_guard()
        check = guard.check(
            output,
            agent_id="sophia",
            context={
                "is_tool_call": bool(tool_calls),
                "require_timestamp": True,
                "session_id": state.session_id,
            },
        )

        # [Phase 1.0.21] Single point of reliability update (EWMA Model Success = 1.0)
        _delta = check["score_delta"] if check["violations"] else 1.0
        _get_meta().adjust_reliability(
            agent_id="sophia",
            delta=_delta,
            violation_type=check["violations"][0] if check["violations"] else "",
            session_id=state.session_id,
        )

        if check["action"] == "reject":
            logger.warning(f"Sophia: Draft rejected by OutputGuard ({check['violations']})")
            return "", []

        if parsed:
            _get_episodic().log(
                session_id=state.session_id,
                agent_id="sophia",
                action="run_draft",
                detail=f"Task: {state.task[:100]}... Tools: {len(tool_calls)}",
                outcome="success",
            )

            # Phase 4: Goal Lifecycle - Mark goal as completed if final response exists
            if parsed.final_response:
                try:
                    from .hephaestus import _get_goals

                    active_goals = _get_goals().list_active(limit=1)
                    if active_goals:
                        # [SRC:axis_3] Completing current goal
                        _get_goals().complete(active_goals[0]["id"])
                        logger.info(
                            f"Sophia: Goal '{active_goals[0]['title']}' marked as COMPLETED."
                        )
                except Exception as ge:
                    logger.warning(f"Sophia: Goal completion trigger failed ({ge})")

        _consecutive_draft_timeouts = 0
        return output, tool_calls
    except TimeoutError:
        _consecutive_draft_timeouts += 1
        logger.error(
            f"Sophia: Draft generation timed out after 60s ({_consecutive_draft_timeouts}x)"
        )
        if _consecutive_draft_timeouts >= 3:
            logger.error("Sophia: 3 consecutive timeouts. GPU likely hung. Raising.")
            raise RuntimeError("Sophia: 3 consecutive draft timeouts. GPU hang suspected.")
        return "", []
    except Exception as e:
        _consecutive_draft_timeouts = 0
        logger.error(f"Sophia: Draft generation failed ({e})", exc_info=True)
        return "", []


@_get_monitor().trace("sophia")
async def run_critique(
    draft: str, session_id: str = "default", model_name: str | None = None
) -> CritiqueResult:
    logger.info(f"Sophia: Auditing Draft in session {session_id}...")
    critique_start = time.time()
    stable, dynamic, _ = await get_dynamic_context("auditor", session_id=session_id)

    # Load Lachesis Skills
    skill_context = ""
    try:
        with open(os.path.join("agent", "lachesis.yaml")) as f:
            cfg = yaml.safe_load(f)
        skills_list = cfg.get("skills", [])
        if skills_list:
            from src.clotho.skill_loader import get_skill_loader

            loader = get_skill_loader()
            summaries = [
                loader.get_skill_summary(s) for s in skills_list if loader.get_skill_summary(s)
            ]
            if summaries:
                skill_context = "ACTIVE SKILLS:\n" + "\n".join([str(s) for s in summaries if s])
    except Exception:
        pass

    context = f"{stable}\n\n{skill_context}\n\n{dynamic}"

    from src.clotho.bootstrap import get_scheduler

    scheduler = get_scheduler()
    # Morpheus: Request a fitting model for the critique role (Axis 7 SSOT)
    from src.architrave.model_registry import resolve_local_model
    model_name = model_name or resolve_local_model("critique", "primary")

    response = await asyncio.wait_for(
        get_ollama_client().chat(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": f"You are the Logical Auditor (Lachesis).\n\nCONTEXT:\n{context}\n\nReturn JSON: is_valid, flaws, suggestions.",
                },
                {"role": "user", "content": f"Review this draft:\n{draft}"},
            ],
        ),
        timeout=30.0,
    )

    # Axis 2: Procedural Log (Tool Tracking)
    _get_procedural().record_usage(
        tool_name="phi-4-mini-ud",
        task_type="critique",
        success=True,
        latency_ms=round((time.time() - critique_start) * 1000, 1),
    )

    content = response["message"]["content"]
    try:
        json_str = extract_first_json_block(content)
        if not json_str:
            return CritiqueResult(
                is_valid=False, flaws=["Parse Error"], suggestions=[content], confidence_score=0.1
            )

        res_data = json.loads(json_str)

        # Confidence calculation (Sovereign L3 Phase 11.19.2)
        flaw_count = len(res_data.get("flaws", []))
        is_valid = res_data.get("is_valid", False)

        conf = 1.0 - (flaw_count * 0.15)
        if not is_valid:
            conf = min(conf, 0.6)

        conf = max(0.1, round(conf, 2))
        res_data["confidence_score"] = conf

        return CritiqueResult(**res_data)
    except Exception as e:
        logger.error(f"Sophia: Critique parsing failed ({e})")
        return CritiqueResult(
            is_valid=False, flaws=[str(e)], suggestions=[content], confidence_score=0.1
        )


@_get_monitor().trace("sophia")
async def run_refine(
    task: str, draft: str, critique: CritiqueResult, session_id: str = "default"
) -> str:
    logger.info(f"Sophia: Refining Solution in session {session_id}...")
    stable, dynamic, _ = await get_dynamic_context("sophia", task_hint=task, session_id=session_id)
    architrave = _get_gateway()

    inst = get_sophia_instructions([])
    critique_str = (
        json.dumps(critique)
        if isinstance(critique, dict)
        else (critique.model_dump_json() if hasattr(critique, "model_dump_json") else str(critique))
    )
    prompt = (
        f"DYNAMIC CONTEXT:\n{dynamic}\n\nTask: {task}\nDraft: {draft}\nCritique: {critique_str}"
    )
    try:
        response = await asyncio.wait_for(
            architrave.generate_async(
                prompt=prompt,
                system_instruction=f"You are the Master Refiner.\n\nSTABLE CONTEXT:\n{stable}\n\n{inst['timestamp']}\n\n{inst['citation']}\n\nProduce the final version, ensuring all claims are cited with [SRC:axis_N].",
                thinking=True,
            ),
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
    # [Phase 1.0.21] Single point of reliability update with EWMA Success = 1.0
    _delta = check["score_delta"] if check["violations"] else 1.0
    _get_meta().adjust_reliability(
        agent_id="sophia",
        delta=_delta,
        violation_type=check["violations"][0] if check["violations"] else "",
        session_id=session_id,
    )

    if check["violations"] and check["action"] == "reject":
        logger.warning(f"Guardrail rejected refine output ({check['violations']}). Retrying.")
        try:
            retry_response = await asyncio.wait_for(
                architrave.generate_async(
                    prompt=prompt,
                    system_instruction=f"You are the Master Refiner.\n\nSTABLE CONTEXT:\n{stable}\n\n{inst['timestamp']}\n\nProduce the final version.",
                    thinking=True,
                ),
                timeout=60.0,
            )
            result_text = retry_response.text
        except (TimeoutError, Exception):
            logger.error("Sophia: Refine retry also failed")
            return draft

    return result_text
