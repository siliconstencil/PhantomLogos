import os
import re

import yaml

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

SKILLS_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "agent", "skills"
)

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


class SkillLoader:
    """
    Loads SKILL.md files from agent/skills/ directory and provides them to the agent pipeline.
    Each skill is a Markdown file with YAML frontmatter for metadata.
    """

    def __init__(self, skills_dir: str = SKILLS_ROOT):
        self.skills_dir = skills_dir
        self._cache: dict[str, dict] = {}
        self._load_all()

    def _parse_frontmatter(self, text: str) -> dict:
        match = FRONTMATTER_PATTERN.match(text)
        if not match:
            return {}
        try:
            return yaml.safe_load(match.group(1)) or {}
        except Exception as e:
            logger.error(f"SkillLoader: YAML parse error in frontmatter: {e}")
            return {}

    def _load_all(self):
        if not os.path.isdir(self.skills_dir):
            logger.warning(f"SkillLoader: Skills directory not found: {self.skills_dir}")
            return
        for entry in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, entry, "SKILL.md")
            if not os.path.isfile(skill_path):
                continue
            try:
                with open(skill_path, encoding="utf-8") as f:
                    content = f.read()
                meta = self._parse_frontmatter(content)
                name = meta.get("name", entry)
                body = FRONTMATTER_PATTERN.sub("", content).strip()
                self._cache[name] = {
                    "path": skill_path,
                    "meta": meta,
                    "body": body,
                }
                logger.info(f"SkillLoader: Loaded skill '{name}' v{meta.get('version', '?')}")
            except Exception as e:
                logger.error(f"SkillLoader: Failed to load {skill_path} ({e})")

    def list_skills(self) -> list[dict]:
        results = []
        for name, info in self._cache.items():
            deps = info["meta"].get("depends-on") or []
            if isinstance(deps, str):
                deps = [deps]

            missing_deps = [d for d in deps if d not in self._cache]
            if missing_deps:
                logger.warning(
                    f"SkillLoader: Skill '{name}' has missing dependencies: {missing_deps}"
                )

            results.append(
                {
                    "name": name,
                    "description": info["meta"].get("description", ""),
                    "version": str(info["meta"].get("version", "")),
                    "dependencies": deps,
                    "missing_dependencies": missing_deps,
                }
            )
        return results

    def get_skill(self, name: str) -> dict | None:
        return self._cache.get(name)

    def get_context(self, name: str) -> str | None:
        info = self._cache.get(name)
        if not info:
            return None
        return f"[Skill: {name}]\n{info['body']}"

    def get_skill_summary(self, name: str) -> str | None:
        """
        Returns a concise 1-line summary for system prompt injection.
        """
        info = self._cache.get(name)
        if not info:
            return None
        meta = info.get("meta", {})
        desc = meta.get("description", "No description provided.")
        ver = meta.get("version", "0.0.0")
        return f"- {name} (v{ver}): {desc}"

    def match_for_task(self, task: str) -> list[str]:
        found = []
        task_lower = task.lower()
        for name, info in self._cache.items():
            body_lower = info["body"].lower()
            desc_lower = info["meta"].get("description", "").lower()
            if any(kw in task_lower for kw in name.split("-")) or any(
                kw in task_lower for kw in desc_lower.split()[:5]
            ):
                found.append(name)
        return found

    def match_for_agent(self, agent_id: str) -> list[str]:
        try:
            from src.clotho.agent_loader import AgentRegistry

            reg = AgentRegistry.get_instance()
            agent = reg.get(agent_id)
            if not agent:
                return []

            found = []
            for s in agent.skills:
                if s in self._cache:
                    found.append(s)
                else:
                    logger.warning(
                        f"SkillLoader: Agent '{agent_id}' references missing skill '{s}'"
                    )
            return found
        except Exception as e:
            logger.warning(f"SkillLoader: Failed to match skills for agent {agent_id} ({e})")
            return []

    def get_allowed_tools_for_agent(self, agent_id: str) -> list[str]:
        """
        SSOT for Tool RBAC. Merges agent-base tools + skill-allowed tools.
        """
        from src.clotho.agent_loader import AgentRegistry

        reg = AgentRegistry.get_instance()
        agent = reg.get(agent_id)
        if not agent:
            return []

        # Base tools
        allowed = set(agent.tools)

        # Add tools from each assigned skill
        for sname in agent.skills:
            info = self._cache.get(sname)
            if info:
                skill_tools = info["meta"].get("allowed-tools") or []
                if isinstance(skill_tools, str):
                    skill_tools = [skill_tools]
                allowed.update(skill_tools)

        return sorted(list(allowed))


_loader_instance = None


def get_skill_loader() -> SkillLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = SkillLoader()
    return _loader_instance
