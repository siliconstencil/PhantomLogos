import asyncio
from typing import Any

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


async def negotiate_node(state: Any):
    """Initial node: negotiate DOD, load agent definition, resolve model."""
    try:
        from src.clotho.bootstrap import start_morpheus

        start_morpheus()

        from cognition.mnemosyne.session_log import SessionLog
        from cognition.sophia.sprint_contract import SprintContract
        from src.clotho.agent_loader import AgentRegistry

        sc = SprintContract(state["session_id"])
        contract = await sc.negotiate(state["task"])

        # [Phase 1.0.21] Goal Lifecycle Restoration (Axis 3)
        try:
            from cognition.mnemosyne.goal_store import GoalStore

            GoalStore().add(title=state["task"][:255], session_id=state["session_id"])
            logger.info("ergon: Goal record created for task.")
        except Exception as ge:
            logger.warning(f"ergon: GoalStore injection failed ({ge})")

        agent_reg = AgentRegistry.get_instance()

        # SOTA 2026: Dynamic Agent Selection (RuFlow Mapping)
        task_lower = state["task"].lower()
        complexity = contract.get("complexity", 0.7)

        if any(
            kw in task_lower for kw in ["audit", "security", "verify", "check", "vulnerability"]
        ):
            agent_id = "lachesis"
        elif complexity >= 0.8 or any(
            kw in task_lower for kw in ["implement", "create", "build", "refactor"]
        ):
            agent_id = "clotho"
        else:
            agent_id = "sophia"

        agent = agent_reg.get(agent_id)
        active_agent = agent.to_dict() if agent else {"id": agent_id, "temperature": 0.1}

        # [Step 1] Skill-First Calibration: Inject relevant skills based on task keywords
        skill_context = ""
        try:
            from src.clotho.skill_loader import SkillLoader

            loader = SkillLoader()
            # Discover skills matching the task using native matching logic
            relevant_skills = loader.match_for_task(task_lower)

            # SOTA 2026: Supplementary calibration for critical tasks
            if "audit" in task_lower:
                relevant_skills.extend(["security-audit", "persona-auditor"])
            elif "refactor" in task_lower:
                relevant_skills.extend(["code-generation", "logic-deadlock-resolver"])

            # Deduplicate and limit to top 10 for context efficiency
            relevant_skills = sorted(list(set(relevant_skills)))[:10]

            if relevant_skills:
                logger.info(f"ergon: Calibrating agent with skills: {relevant_skills}")
                fragments = []
                for sk_name in relevant_skills:
                    content = loader.get_skill_summary(sk_name)
                    if content:
                        fragments.append(content)
                
                skill_context = "\n\n## Calibrated Competencies\n" + "\n".join(fragments)
            else:
                # Default safety skill
                skill_context = "\n\n## Calibrated Competencies\n" + (loader.get_skill_summary("error-self-recovery") or "")

        except Exception as se:
            logger.warning(f"ergon: Skill-First calibration failed ({se})")

        log = SessionLog(state["session_id"])
        history = log.get_history(limit=1)
        sync_ok = len(history) > 0

        # Merge Attack: VRAM + Reliability override for tier selection
        try:
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore
            from src.clotho.bootstrap import quick_vram_check

            vram = await asyncio.to_thread(quick_vram_check)
            free_gb = vram.get("free_gb", 7.0)
            rel = await asyncio.to_thread(MetaCognitionStore().get_reliability, "sophia")
            if free_gb < 2.0 or rel < 0.3:
                tier = 0 if free_gb < 1.0 else 1
                model_tier = "ultra_light" if tier == 0 else "light"
                logger.warning(
                    f"ergon: Forced Tier {tier} (VRAM={free_gb}GB, reliability={rel:.2f})"
                )
            else:
                if complexity < 0.3:
                    tier = 0
                    model_tier = "ultra_light"
                elif complexity < 0.5:
                    tier = 1
                    model_tier = "light"
                elif complexity <= 0.8 and free_gb >= 3.0:
                    tier = 2
                    model_tier = "primary"
                else:
                    tier = 3 if free_gb >= 5.0 else 2
                    model_tier = "expert" if free_gb >= 5.0 else "primary"
        except Exception as e:
            logger.warning(f"ergon: VRAM/reliability check failed, using complexity-only ({e})")
            if complexity < 0.3:
                tier = 0
                model_tier = "ultra_light"
            elif complexity < 0.5:
                tier = 1
                model_tier = "light"
            else:
                tier = 2 if complexity <= 0.8 else 3
                model_tier = "primary" if complexity <= 0.8 else "expert"

        logger.info(f"ergon: Agent '{active_agent['id']}' Tier={tier} ({model_tier})")

        try:
            from cognition.mnemosyne.operational_store import OperationalStore

            OperationalStore().record_event(
                name="session.init",
                level="INFO",
                message=f"Session started with agent '{active_agent['id']}' at Tier {tier}",
                agent_id=active_agent["id"],
                session_id=state["session_id"],
            )
        except Exception as oe:
            logger.warning(f"ergon: Failed to record session init event ({oe})")

        return {
            "contract": contract,
            "memory_sync": sync_ok,
            "active_agent": active_agent,
            "calibrated_skills": skill_context,
            "ru_flow_tier": tier,
            "selected_model_tier": model_tier,
            "ru_flow_active": (tier == 3),
            "verification_retry": 0,
        }
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"ergon: negotiate_node failed ({e})", exc_info=True)
        return {"contract": {"threshold": 0.5}, "memory_sync": False, "active_agent": None}
