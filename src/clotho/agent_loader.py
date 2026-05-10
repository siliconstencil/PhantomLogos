import os
import yaml
from typing import Dict, Optional, Any, List
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

AGENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "agent")


class AgentDefinition:
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.version: str = data.get("version", "0.0.0")
        self.description: str = data.get("description", "")
        self.temperature: float = data.get("temperature", 0.3)
        self.max_iterations: int = data.get("max_iterations", 1)
        self.system_prompt: str = data.get("system_prompt", "")
        self.tools: List[str] = data.get("tools", [])
        self.skills: List[str] = data.get("skills", [])
        self.memory_axes: List[int] = data.get("memory_axes", [])
        self.guardrails: List[str] = data.get("guardrails", [])

        self.capability: Optional[str] = data.get("capability")

        model_cfg = data.get("model", {})
        self.model_primary: Optional[str] = model_cfg.get("primary") if model_cfg else None
        self.model_fallback: Optional[str] = model_cfg.get("fallback") if model_cfg else None

    def resolve_primary_model(self) -> Optional[str]:
        from src.architrave.model_registry import resolve_capability, resolve_model
        if self.capability:
            cap_model = resolve_capability(self.capability)
            if cap_model:
                return cap_model
        if self.model_primary:
            return resolve_model(self.model_primary)
        return None

    def resolve_temperature(self, role: str) -> float:
        try:
            from cognition.sophia.temperature_control import get_temperature
            return get_temperature(role)
        except Exception as e:
            logger.warning(f"AgentDefinition: Failed to get dynamic temperature ({e}). Using default: {self.temperature}")
            return self.temperature

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "capability": self.capability,
            "model_primary": self.resolve_primary_model(),
            "model_fallback": self.model_fallback,
            "temperature": self.temperature,
            "tools": self.tools,
            "skills": self.skills,
            "memory_axes": self.memory_axes,
        }


class AgentRegistry:
    _instance = None

    def __init__(self, agent_dir: str = AGENT_DIR):
        self.agent_dir = agent_dir
        self._agents: Dict[str, AgentDefinition] = {}
        self._load_all()

    @classmethod
    def get_instance(cls, agent_dir: str = AGENT_DIR) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = cls(agent_dir)
        return cls._instance

    def _load_all(self):
        if not os.path.isdir(self.agent_dir):
            logger.warning(f"AgentRegistry: Agent dir not found: {self.agent_dir}")
            return
        for fname in sorted(os.listdir(self.agent_dir)):
            if not fname.endswith((".yaml", ".yml")):
                continue
            fpath = os.path.join(self.agent_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data or "id" not in data:
                    logger.warning(f"AgentRegistry: Skipping {fname} (no 'id' field)")
                    continue
                agent_id = data["id"]
                self._agents[agent_id] = AgentDefinition(data)
                logger.info(f"AgentRegistry: Loaded agent '{agent_id}' v{data.get('version', '0.0.0')}")
            except Exception as e:
                logger.error(f"AgentRegistry: Failed to load {fname} ({e})")

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        return self._agents.get(agent_id)

    def get_by_role(self, role: str) -> Optional[AgentDefinition]:
        role_map = {
            "sophia": "sophia",
            "planner": "sophia",
            "strategist": "sophia",
            "clotho": "clotho",
            "executor": "clotho",
            "lachesis": "lachesis",
            "auditor": "lachesis",
            "critic": "lachesis",
            "atropos": "atropos",
            "pruner": "atropos",
            "morpheus": "morpheus",
            "resource": "morpheus",
        }
        aid = role_map.get(role.lower(), role.lower())
        return self._agents.get(aid)

    def list_agents(self) -> List[dict]:
        return [a.to_dict() for a in self._agents.values()]

    def get_tools_for(self, agent_id: str) -> List[str]:
        agent = self.get(agent_id)
        return agent.tools if agent else []

    def get_skills_for(self, agent_id: str) -> List[str]:
        agent = self.get(agent_id)
        return agent.skills if agent else []

    def resolve_model(self, agent_id: str, use_fallback: bool = False) -> Optional[str]:
        agent = self.get(agent_id)
        if not agent:
            return None
        if use_fallback and agent.model_fallback:
            from src.architrave.model_registry import resolve_model as _resolve_alias
            return _resolve_alias(agent.model_fallback)
        return agent.resolve_primary_model()
