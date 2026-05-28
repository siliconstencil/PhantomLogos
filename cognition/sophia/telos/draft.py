import asyncio
import json
import os

import yaml

from src.lachesis import get_output_guard
from src.utils.logging_config import setup_logger

from ..eidos import ReasoningState, SophiaOutput
from ..gnosis import get_dynamic_context
from ..hephaestus import (
    _get_episodic,
    _get_goals,
    _get_meta,
    _get_monitor,
    get_sophia_instructions,
    strip_thinking_block,
)
from ._gateway import _get_gateway

logger = setup_logger(__name__)

_consecutive_draft_timeouts = 0


@_get_monitor().trace("sophia")
async def run_draft(state: ReasoningState, thinking: bool = True) -> str | tuple:
    global _consecutive_draft_timeouts
    if isinstance(state, dict):
        state = ReasoningState(**state)
    logger.info(f"Sophia: Generating Draft (Thinking Mode: {thinking})...")
    stable, dynamic, block_signal = await get_dynamic_context(
        "sophia", task_hint=state.task, session_id=state.session_id
    )

    fallback_model = None
    if block_signal["block"]:
        if hasattr(state, "flags") and state.flags.get("bypass_memory_gate"):
            logger.info("Sophia: Hard Gate bypassed via L0 Force Override")
        elif block_signal.get("fallback_model"):
            logger.warning(
                f"Sophia: Token budget exceeded. Routing to local fallback model: {block_signal['fallback_model']}"
            )
            fallback_model = block_signal["fallback_model"]
        else:
            logger.warning(f"Sophia: Hard Gate Triggered - {block_signal['reason']}")
            return (
                f"HARD GATE: Task blocked due to previous failures. Reason: {block_signal['reason']}",
                [],
            )

    try:
        with open(os.path.join("agent", "sophia.yaml")) as f:
            cfg = yaml.safe_load(f)
        tools = cfg.get("tools", [])
        skills_list = cfg.get("skills", [])
    except Exception:
        tools = ["ls", "semantic", "mapper", "vram", "report"]
        skills_list = []

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

    governing_rules = ""
    try:
        with open(os.path.join(".antigravity", "rules.json")) as f:
            rules_data = json.load(f)
        rules_list = rules_data.get("governance_rules", [])
        task_lower = state.task.lower()
        if any(kw in task_lower for kw in ["code", "file", "write", "edit", "delete"]):
            target_ids = {
                "RULE-030",
                "RULE-031",
                "RULE-037",
                "BA-01",
                "EMOJI_BAN",
                "TIMESTAMP_RULE",
                "PRE_FLIGHT_AUDIT",
                "BACKUP_BEFORE_WRITE",
                "SOVEREIGN_DELETION_GATE",
                "L0_AUTH_PROTOCOL",
            }
        elif any(kw in task_lower for kw in ["model", "vram", "memory", "gpu", "load", "ollama"]):
            target_ids = {
                "VRAM_HYGIENE",
                "SEQUENTIAL_LOADING",
                "DYNAMIC_OFFLOADING",
                "RULE-034",
                "RULE-030",
                "RESOURCE_HYGIENE",
                "OLLAMA_SELF_HEALING",
            }
        elif any(
            kw in task_lower
            for kw in ["refactor", "strategic", "plan", "architecture", "design", "restructure"]
        ):
            target_ids = {
                "SOCRATIC_INQUIRY",
                "ABSOLUTE_AGNOSTICISM",
                "RULE-030",
                "RULE-032",
                "RULE-033",
                "CITATION_MANDATE",
                "LACONISM_MANDATE",
                "MANDATORY_FORMAL_AUDIT",
            }
        elif any(
            kw in task_lower for kw in ["semantic", "recall", "remember", "search", "retrieve"]
        ):
            target_ids = {"RULE-036", "CITATION_MANDATE", "MEMORY_CONTINUITY", "DUAL_PATH_FALLBACK"}
        else:
            target_ids = {"LACONISM_MANDATE", "EMOJI_BAN", "TIMESTAMP_RULE", "RULE-030"}
        relevant = [
            f"  - {r['id']}: {r['description']}" for r in rules_list if r.get("id") in target_ids
        ]
        if relevant:
            governing_rules = "GOVERNING RULES:\n" + "\n".join(relevant)
    except Exception as e:
        logger.warning(f"Sophia: Governing rules injection failed ({e})")

    inst = get_sophia_instructions(tools)
    architrave = _get_gateway()

    session_id = getattr(state, "session_id", None) or "default"

    try:
        rules_section = f"GOVERNING RULES:\n{governing_rules}\n\n" if governing_rules else ""
        prompt_text = (
            f"{rules_section}"
            f"FAILURE AWARENESS MANDATE (Axis 8):\n"
            f"Review Axis 8 in the dynamic context below. You MUST NOT repeat previous failure patterns.\n\n"
            f"DYNAMIC CONTEXT:\n{dynamic}\n\n"
            f"TASK:\n{state.task}"
        )
        sys_instruction = f"You are the Sovereign Architect (Sophia) of Phantom Logos.\n\nSTABLE CONTEXT (GOVERNANCE):\n{stable}\n\n{skill_context}\n\n{inst['timestamp']}\n\n{inst['tool']}\n\n{inst['citation']}\n\nProvide a high-performance solution based on the 14-axis memory state."

        legacy_cloud_first = False

        if legacy_cloud_first:
            if fallback_model:
                response = await architrave._local_fallback(
                    prompt=prompt_text,
                    system_instruction=sys_instruction,
                    thoughts="Token budget fallback route.",
                    model=fallback_model,
                )
            else:
                generate_kwargs = dict(
                    prompt=prompt_text,
                    system_instruction=sys_instruction,
                    thinking=thinking,
                    response_schema=SophiaOutput,
                    response_mime_type="application/json",
                    session_id=session_id,
                )
                response = await asyncio.wait_for(
                    architrave.generate_async(**generate_kwargs),
                    timeout=60.0,
                )
        else:
            tier = 2
            if hasattr(state, "flags") and isinstance(state.flags, dict):
                tier = state.flags.get("tier", 2)
            elif isinstance(state, dict):
                tier = state.get("ru_flow_tier", 2)
            elif hasattr(state, "ru_flow_tier"):
                tier = getattr(state, "ru_flow_tier", 2)

            vram_threshold = 2.0
            available_vram = 6.0
            try:
                from cognition.morpheus.monitor import get_gpu_memory_info

                gpu_info = get_gpu_memory_info()
                available_vram = gpu_info.get("free_gb", 6.0)
                if available_vram < vram_threshold:
                    logger.warning(
                        f"Sophia: Available VRAM ({available_vram:.2f} GB) below threshold ({vram_threshold} GB). Forcing Tier 0 (Ultra-Light)."
                    )
                    tier = 0
            except Exception as ve:
                logger.warning(f"Sophia: VRAM monitor check bypassed ({ve})")

            sys_instruction += '\n\nYou MUST return a single JSON object matching this schema:\n{\n  "thought": "your internal reasoning process",\n  "technical_claims": [],\n  "tool_calls": [],\n  "final_response": "your response content"\n}'

            if fallback_model:
                logger.warning(f"Sophia: Fallback model active: {fallback_model}")
                response = await architrave._local_fallback(
                    prompt=prompt_text,
                    system_instruction=sys_instruction,
                    thoughts="Token budget fallback route.",
                    model=fallback_model,
                )
            elif tier == 0:
                logger.info("Sophia: Tier 0 Routing (Ultra-Light) -> deepscaler-1.5b:latest")
                response = await architrave._local_fallback(
                    prompt=prompt_text,
                    system_instruction=sys_instruction,
                    thoughts="Tier 0 ultra-light local execution.",
                    model="deepscaler-1.5b:latest",
                )
            elif tier == 1:
                logger.info("Sophia: Tier 1 Routing (Light) -> ministral-3b-ud:latest")
                response = await architrave._local_fallback(
                    prompt=prompt_text,
                    system_instruction=sys_instruction,
                    thoughts="Tier 1 light local execution.",
                    model="ministral-3b-ud:latest",
                )
            elif tier == 2:
                from src.architrave.model_registry import find_fitting_model
                from src.clotho.krisis import is_tool_dispatch_task
                from src.clotho.skill_loader import get_skill_loader

                if is_tool_dispatch_task(state.task):
                    logger.info(
                        "Sophia: Tier 2 Tool Dispatch detected. Using FunctionGemma (0.3 GB) instead of skill-matched model."
                    )
                    response = await architrave._local_fallback(
                        prompt=prompt_text,
                        system_instruction=sys_instruction,
                        thoughts="Tier 2 tool dispatch routing via FunctionGemma.",
                        model="functiongemma-270m:latest",
                    )
                else:
                    loader = get_skill_loader()
                    matched = loader.match_for_task(state.task)

                    role = "primary"
                    for sname in matched:
                        skill_info = loader.get_skill(sname)
                        if skill_info:
                            role = skill_info.get("meta", {}).get("model_role", "primary")
                            break

                    model_name = find_fitting_model(role, available_vram)
                    logger.info(
                        f"Sophia: Tier 2 Routing -> Skill matching role '{role}' -> Model: '{model_name}'"
                    )
                    response = await architrave._local_fallback(
                        prompt=prompt_text,
                        system_instruction=sys_instruction,
                        thoughts=f"Tier 2 skill-based local execution for role: {role}",
                        model=model_name,
                    )
            elif tier == 3:
                is_strategic = False
                task_lower = state.task.lower()
                if any(
                    kw in task_lower
                    for kw in [
                        "refactor",
                        "architecture",
                        "strategic",
                        "restructure",
                        "constitution",
                        "design",
                        "plan",
                    ]
                ):
                    is_strategic = True

                if is_strategic:
                    logger.info("Sophia: Tier 3 Strategic Task. Routing to Cloud Gateway.")
                    generate_kwargs = dict(
                        prompt=prompt_text,
                        system_instruction=sys_instruction,
                        thinking=thinking,
                        response_schema=SophiaOutput,
                        response_mime_type="application/json",
                        session_id=session_id,
                    )
                    response = await asyncio.wait_for(
                        architrave.generate_async(**generate_kwargs),
                        timeout=60.0,
                    )
                else:
                    from src.architrave.model_registry import find_fitting_model

                    expert_model = find_fitting_model("expert", available_vram)
                    logger.info(
                        f"Sophia: Tier 3 Non-Strategic Task. Downgrading to Tier 2 Local Expert Model -> '{expert_model}'"
                    )
                    response = await architrave._local_fallback(
                        prompt=prompt_text,
                        system_instruction=sys_instruction,
                        thoughts="Tier 3 non-strategic task local downgrade.",
                        model=expert_model,
                    )
            else:
                logger.info(
                    f"Sophia: Unknown Tier ({tier}). Defaulting to Tier 2 (Standard L2 Runner) -> qwen3.5-4b-ud:latest"
                )
                response = await architrave._local_fallback(
                    prompt=prompt_text,
                    system_instruction=sys_instruction,
                    thoughts="Unknown tier standard fallback.",
                    model="qwen3.5-4b-ud:latest",
                )

        output = response.text
        clean_text = strip_thinking_block(output)

        if output.startswith("[SYSTEM GUARD]"):
            logger.warning("Sophia: System Guard message detected. Bypassing JSON parse.")
            return output, []

        parsed = None
        try:
            parsed = SophiaOutput.model_validate_json(clean_text)
        except Exception:
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
            except Exception:
                pass

        if parsed is None:
            logger.error("Sophia: Model failed to provide structured JSON. REJECTING.")
            return "", []

        try:
            tool_calls = parsed.tool_calls
            logger.info(
                f"Sophia: Parsed structured output with {len(tool_calls)} tool calls and {len(parsed.technical_claims)} claims"
            )
        except Exception as pe:
            logger.error(f"Sophia: Schema validation failed ({pe}). Output: {clean_text[:100]}...")
            return "", []

        if tool_calls and parsed and parsed.technical_claims:
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

            if parsed.final_response:
                try:
                    active_goals = _get_goals().list_active(limit=1)
                    if active_goals:
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
