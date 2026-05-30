# [SRC:axis_13] FederationBridge - Clotho-level A2A messaging interface
import asyncio
import os
from typing import Any

from src.architrave.a2a.auth import get_secret_for_agent
from src.architrave.a2a.client import send_a2a_message
from src.architrave.a2a.discovery import A2ADiscovery
from src.architrave.a2a.protocol import BusMessage
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class FederationBridge:
    """Bidirectional bridge between Clotho orchestrator and A2A federated agents.
    Enables GraphState-aware messaging to remote agents for distributed task execution.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        local_endpoint: str | None = None,
        discovery: A2ADiscovery | None = None,
    ) -> None:
        self.agent_id = agent_id or os.getenv("A2A_AGENT_ID", "sophia")
        self.local_endpoint = local_endpoint or os.getenv(
            "A2A_LOCAL_ENDPOINT", "http://localhost:32554"
        )
        self.discovery = discovery or A2ADiscovery()
        self._lock = asyncio.Lock()

    async def send_to_agent(
        self,
        recipient: str,
        topic: str,
        payload: dict[str, Any],
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        """Send a message to a specific federated agent by agent_id."""
        agent = self.discovery.resolve(recipient)
        if not agent:
            logger.warning(
                f"FederationBridge: Unknown agent '{recipient}' - checking file registry"
            )
            self.discovery._load_from_file()
            agent = self.discovery.resolve(recipient)
            if not agent:
                return {"status": "error", "error": f"Unknown agent: {recipient}"}

        secret = get_secret_for_agent(recipient)
        msg = BusMessage(
            sender=self.agent_id,
            recipient=recipient,
            topic=topic,
            payload=payload,
        )

        return await send_a2a_message(
            target_endpoint=agent.endpoint,
            msg=msg,
            secret=secret,
            sender_endpoint=self.local_endpoint,
            timeout_s=timeout_s,
        )

    async def broadcast(
        self,
        topic: str,
        payload: dict[str, Any],
        timeout_s: float = 10.0,
    ) -> list[dict[str, Any]]:
        """Broadcast a message to all online federated agents."""
        async with self._lock:
            agents = self.discovery.list_online_agents()
            if not agents:
                logger.info("FederationBridge: No online agents to broadcast to.")
                return []

            secret = self._get_local_secret()
            results: list[dict[str, Any]] = []
            for agent in agents:
                msg = BusMessage(
                    sender=self.agent_id,
                    recipient=agent.agent_id,
                    topic=topic,
                    payload=payload,
                )
                try:
                    result = await send_a2a_message(
                        target_endpoint=agent.endpoint,
                        msg=msg,
                        secret=secret,
                        sender_endpoint=self.local_endpoint,
                        timeout_s=timeout_s,
                    )
                    results.append({"agent": agent.agent_id, "result": result})
                except Exception as e:
                    logger.error(f"FederationBridge: Broadcast to '{agent.agent_id}' failed ({e})")
                    results.append(
                        {"agent": agent.agent_id, "result": {"status": "error", "error": str(e)}}
                    )

            return results

    async def send_graph_state(
        self,
        recipient: str,
        state: dict[str, Any],
        topic: str = "graph_state",
    ) -> dict[str, Any]:
        """Send a serialized GraphState snapshot to a federated agent for remote processing."""
        safe_state = {
            k: v
            for k, v in state.items()
            if k in {"task", "draft", "final_output", "iteration", "session_id"}
        }
        return await self.send_to_agent(recipient, topic, {"graph_state": safe_state})

    async def request_reasoning(
        self,
        recipient: str,
        task: str,
        context: dict[str, Any] | None = None,
        timeout_s: float = 30.0,
    ) -> dict[str, Any]:
        """Request remote agent to perform reasoning on a task and return a result."""
        payload: dict[str, Any] = {"task": task}
        if context:
            payload["context"] = context
        return await self.send_to_agent(
            recipient, "reasoning_request", payload, timeout_s=timeout_s
        )

    def _get_local_secret(self) -> str:
        return get_secret_for_agent(self.agent_id)
