import asyncio
import json
import os
import time
from collections.abc import Callable
from typing import ClassVar

import httpx

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class RemoteAgentInfo:
    def __init__(self, data: dict) -> None:
        self.agent_id: str = data.get("agent_id", "")
        self.name: str = data.get("name", "")
        self.endpoint: str = data.get("endpoint", "")
        self.capabilities: list[str] = data.get("capabilities", [])
        self.skills: list[str] = data.get("skills", [])
        self.status: str = data.get("status", "offline")
        self.last_heartbeat: float = data.get("last_heartbeat", 0.0)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "skills": self.skills,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
        }


class A2ADiscovery:
    _on_register_callbacks: ClassVar[list] = []

    @classmethod
    def register_on_register_callback(cls, callback: Callable) -> None:
        cls._on_register_callbacks.append(callback)

    def __init__(self, registry_path: str = os.path.join("agent", "a2a_registry.json")) -> None:
        self.registry_path = registry_path
        self._agents: dict[str, RemoteAgentInfo] = {}
        self._heartbeat_task: asyncio.Task | None = None
        self._load_from_file()

    def _load_from_file(self) -> None:
        """
        Load remote agents from the JSON registry file.
        """
        if not os.path.exists(self.registry_path):
            logger.warning(
                f"A2A Discovery: Registry file not found: '{self.registry_path}'. Starting empty."
            )
            return

        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = json.load(f)

            for agent_data in data.get("agents", []):
                agent_id = agent_data.get("agent_id")
                if agent_id:
                    info = RemoteAgentInfo(agent_data)
                    self._agents[agent_id] = info
                    self._sync_with_agent_registry(info)

            logger.info(
                f"A2A Discovery: Loaded {len(self._agents)} agents from '{self.registry_path}'."
            )
        except Exception as e:
            logger.error(
                f"A2A Discovery: Failed to parse registry file '{self.registry_path}' ({e})"
            )

    def _save_to_file(self) -> None:
        """
        Save the current set of remote agents back to the JSON registry file.
        """
        try:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            data = {"agents": [agent.to_dict() for agent in self._agents.values()]}
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(
                f"A2A Discovery: Failed to save registry to file '{self.registry_path}' ({e})"
            )

    def _sync_with_agent_registry(self, info: RemoteAgentInfo) -> None:
        """
        Invoke all registered bridge callbacks to sync remote agents with upper layer registries.
        """
        for callback in self._on_register_callbacks:
            try:
                callback(info)
            except Exception as e:
                logger.error(f"A2A Discovery: Failed to execute registration callback ({e})")

    def register_remote(self, info: RemoteAgentInfo) -> None:
        """
        Manually register a remote agent and sync it with registry.
        """
        self._agents[info.agent_id] = info
        self._sync_with_agent_registry(info)
        self._save_to_file()
        logger.info(
            f"A2A Discovery: Manually registered remote agent '{info.agent_id}' at '{info.endpoint}'."
        )

    def resolve(self, agent_id: str) -> RemoteAgentInfo | None:
        """
        Resolve a remote agent by its agent_id.
        """
        return self._agents.get(agent_id)

    def list_online_agents(self) -> list[RemoteAgentInfo]:
        """
        Return a list of all remote agents currently marked online.
        """
        return [agent for agent in self._agents.values() if agent.status == "online"]

    async def ping_agent(self, agent: RemoteAgentInfo) -> bool:
        """
        Ping a remote agent's health endpoint.
        """
        try:
            url = agent.endpoint.rstrip("/")
            if not url.endswith("/a2a/health"):
                url = f"{url}/a2a/health"

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=4.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "alive":
                        agent.status = "online"
                        agent.last_heartbeat = time.time()
                        return True
        except Exception as e:
            logger.debug(f"A2ADiscovery: heartbeat probe failed ({e})")
        return False

    async def start_heartbeat(self, interval_s: float = 60.0) -> None:
        """
        Starts the background async heartbeat loop.
        """
        if self._heartbeat_task and not self._heartbeat_task.done():
            return

        async def loop() -> None:
            logger.info(f"A2A Discovery: Starting heartbeat loop with {interval_s}s interval.")
            while True:
                try:
                    for agent in list(self._agents.values()):
                        # We don't self-ping our own agent if running local loop, but ping remote agents
                        success = await self.ping_agent(agent)
                        if (
                            not success
                            and time.time() - agent.last_heartbeat > 120.0
                            and agent.status != "offline"
                        ):
                            logger.warning(
                                f"A2A Discovery: Agent '{agent.agent_id}' TTL expired. Marking OFFLINE."
                            )
                            agent.status = "offline"
                    self._save_to_file()
                except Exception as e:
                    logger.error(f"A2A Discovery: Exception in heartbeat loop ({e})")
                await asyncio.sleep(interval_s)

        self._heartbeat_task = asyncio.create_task(loop())

    def stop_heartbeat(self) -> None:
        """
        Stops the heartbeat loop.
        """
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            logger.info("A2A Discovery: Heartbeat loop stopped.")
