import asyncio
from typing import Any
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

async def negotiate_node(state: Any):
    """Initial node: negotiate DOD, load agent definition, resolve model."""
    try:
        from src.clotho.bootstrap import start_morpheus
        start_morpheus()

        from cognition.sophia.sprint_contract import SprintContract
        from src.clotho.agent_loader import AgentRegistry
        from cognition.mnemosyne.session_log import SessionLog

        sc = SprintContract(state["session_id"])
        contract = await sc.negotiate(state["task"])

        agent_reg = AgentRegistry.get_instance()
        
        # SOTA 2026: Dynamic Agent Selection (RuFlow Mapping)
        task_lower = state["task"].lower()
        complexity = contract.get("complexity", 0.7)
        
        if any(kw in task_lower for kw in ["audit", "security", "verify", "check", "vulnerability"]):
            agent_id = "lachesis"
        elif complexity >= 0.8 or any(kw in task_lower for kw in ["implement", "create", "build", "refactor"]):
            agent_id = "clotho"
        else:
            agent_id = "sophia"
            
        agent = agent_reg.get(agent_id)
        active_agent = agent.to_dict() if agent else {"id": agent_id, "temperature": 0.1}

        log = SessionLog(state["session_id"])
        history = log.get_history(limit=1)
        sync_ok = len(history) > 0

        # Merge Attack: VRAM + Reliability override for tier selection
        try:
            from src.clotho.bootstrap import quick_vram_check
            from cognition.mnemosyne.meta_cognition import MetaCognitionStore
            vram = await asyncio.to_thread(quick_vram_check)
            free_gb = vram.get("free_gb", 7.0)
            rel = await asyncio.to_thread(MetaCognitionStore().get_reliability, "sophia")
            if free_gb < 2.0 or rel < 0.3:
                tier = 1
                model_tier = "light"
                logger.warning(f"ergon: Forced Tier 1 (VRAM={free_gb}GB, reliability={rel:.2f})")
            else:
                if complexity < 0.5:
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
            tier = 1 if complexity < 0.5 else (2 if complexity <= 0.8 else 3)
            model_tier = "light" if complexity < 0.5 else ("primary" if complexity <= 0.8 else "expert")

        logger.info(
            f"ergon: Agent '{active_agent['id']}' Tier={tier} ({model_tier})"
        )

        try:
            from cognition.mnemosyne.operational_store import OperationalStore
            OperationalStore().record_event(
                name="session.init",
                level="INFO",
                message=f"Session started with agent '{active_agent['id']}' at Tier {tier}",
                agent_id=active_agent['id'],
                session_id=state["session_id"]
            )
        except Exception as oe:
            logger.warning(f"ergon: Failed to record session init event ({oe})")

        return {
            "contract": contract, 
            "memory_sync": sync_ok, 
            "active_agent": active_agent,
            "ru_flow_tier": tier,
            "selected_model_tier": model_tier,
            "ru_flow_active": (tier == 3),
            "verification_retry": 0
        }
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"ergon: negotiate_node failed ({e})", exc_info=True)
        return {"contract": {"threshold": 0.5}, "memory_sync": False, "active_agent": None}
