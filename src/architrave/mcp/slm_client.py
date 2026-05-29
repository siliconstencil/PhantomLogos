import os
import threading
import time
from dataclasses import dataclass

from src.utils.logging_config import setup_logger

from .mcp_registry import get_mcp_registry

logger = setup_logger(__name__)


class SLMHeartbeatCache:
    """15s TTL, thread-safe heartbeat cache for SLM. 60s backoff after failure."""

    def __init__(self, ttl: float = 15.0) -> None:
        self._ttl = ttl
        self._last_check = 0.0
        self._last_result = False
        self._lock = threading.Lock()
        self._fail_until = 0.0

    @property
    def healthy(self) -> bool:
        with self._lock:
            return self._last_result

    def needs_refresh(self) -> bool:
        with self._lock:
            now = time.time()
            if not self._last_result and now < self._fail_until:
                return False
            return (now - self._last_check) > self._ttl

    def update(self, result: bool) -> None:
        with self._lock:
            self._last_result = result
            self._last_check = time.time()
            if not result:
                self._fail_until = time.time() + 60.0


_heartbeat = SLMHeartbeatCache()

import base64
import contextlib
import json
import struct


def _serialize_vector(vector) -> str:
    vector = vector.tolist() if hasattr(vector, "tolist") else list(vector)
    vec_bytes = struct.pack(f"{len(vector)}f", *vector)
    return base64.b64encode(vec_bytes).decode("ascii")


def _deserialize_vector(v_b64: str) -> list:
    vec_bytes = base64.b64decode(v_b64)
    n = len(vec_bytes) // 4
    return list(struct.unpack(f"{n}f", vec_bytes))


def _serialize_meta(meta: dict) -> str:
    return json.dumps(meta)


def _deserialize_meta(m_json: str) -> dict:
    try:
        return json.loads(m_json)
    except Exception:
        return {}


def _flatten_meta_tags(meta: dict) -> list[str]:
    tags = []
    for k, v in meta.items():
        if v is None:
            continue
        tags.append(f"meta:{k}:{v}")
    return tags


def _normalize_result(raw: dict) -> dict:
    tags = raw.get("tags") or []
    content = raw.get("content") or raw.get("text") or ""

    vector = []
    metadata = {}
    timestamp = 0.0
    agent_id = "system"
    axis_id = 6

    for tag in tags:
        if tag.startswith("v:"):
            with contextlib.suppress(Exception):
                vector = _deserialize_vector(tag[2:])
        elif tag.startswith("m:"):
            try:
                legacy_meta = _deserialize_meta(tag[2:])
                if isinstance(legacy_meta, dict):
                    metadata.update(legacy_meta)
            except Exception as e:
                logger.debug(f"SLMClient: legacy meta deserialize skipped ({e})")
        elif tag.startswith("meta:"):
            parts = tag[5:].split(":", 1)
            if len(parts) == 2:
                metadata[parts[0]] = parts[1]
        elif tag.startswith("t:"):
            with contextlib.suppress(Exception):
                timestamp = float(tag[2:])
        elif tag.startswith("a:"):
            agent_id = tag[2:]
        elif tag.startswith("x:"):
            with contextlib.suppress(Exception):
                axis_id = int(tag[2:])

    return {
        "vector": vector,
        "text": content,
        "prevention_rule": content,
        "session_id": raw.get("session_id") or "default",
        "metadata": json.dumps(metadata) if isinstance(metadata, dict) else str(metadata),
        "importance": float(raw.get("importance", 0.5)),
        "timestamp": timestamp,
        "error_type": raw.get("error_type") or metadata.get("error_type") or "unknown",
        "context_hash": metadata.get("context_hash") or "unknown",
        "agent_id": agent_id,
        "axis_id": axis_id,
    }


@dataclass
class SLMConfig:
    mcp_cmd: str = "slm mcp"
    mcp_timeout: int = 30
    endpoint: str = "http://localhost:8081"  # Legacy field for backwards compatibility in tests


class SLMClient:
    def __init__(self, config: SLMConfig | None = None) -> None:
        self.config = config or SLMConfig(
            mcp_cmd=os.getenv("SLM_MCP_CMD", "slm mcp"),
            mcp_timeout=int(os.getenv("SLM_MCP_TIMEOUT", "30")),
        )

    def _get_session(self):
        registry = get_mcp_registry()
        session = registry.get_session("slm")
        if session is None:
            from .mcp_session import MCPSession

            registry._sessions["slm"] = MCPSession(
                name="slm",
                command=self.config.mcp_cmd.split()[0]
                if " " in self.config.mcp_cmd
                else self.config.mcp_cmd,
                args=self.config.mcp_cmd.split()[1:] if " " in self.config.mcp_cmd else [],
                timeout=self.config.mcp_timeout,
                enabled=True,
            )
            session = registry.get_session("slm")
        if session is None:
            raise RuntimeError("SLM MCP Server session is disabled or not initialized")
        return session

    def health(self) -> bool:
        if not _heartbeat.needs_refresh():
            return _heartbeat.healthy

        try:
            session = self._get_session()
            if not session.enabled:
                session.enabled = True
                import threading

                threading.Thread(target=session._ensure_connected, daemon=True).start()
            res = session.call_tool_sync("get_status", {})
            is_ok = isinstance(res, dict) and res.get("status") == "healthy"
            _heartbeat.update(is_ok)
            return is_ok
        except Exception:
            _heartbeat.update(False)
            return False

    def search(
        self,
        query: str,
        limit: int = 5,
        table_name: str | None = None,
        session_id: str | None = None,
    ) -> list[dict]:
        project = table_name or "default"
        params = {"query": query, "limit": limit, "project": project}
        if session_id:
            params["session_id"] = session_id

        try:
            session = self._get_session()
            res = session.call_tool_sync("recall", params)
            raw_results = []
            if isinstance(res, dict):
                raw_results = res.get("results", [])
            elif isinstance(res, list):
                raw_results = res

            filtered = []
            for r in raw_results:
                norm = _normalize_result(r)
                if session_id:
                    if norm["session_id"] in (session_id, "system", "default", "global"):
                        filtered.append(norm)
                else:
                    filtered.append(norm)
            return filtered
        except Exception as e:
            logger.error(f"SLMClient.search failed: {e}")
            return []

    def remember(
        self,
        entry: dict,
        table_name: str | None = None,
        agent_id: str = "system",
        axis_id: int = 6,
    ) -> bool:
        try:
            content = entry.get("text") or entry.get("prevention_rule") or ""

            tags = []
            vector = entry.get("vector")
            if vector is not None:
                tags.append(f"v:{_serialize_vector(vector)}")

            meta = entry.get("metadata") or {}
            if isinstance(meta, dict):
                tags.extend(self._flatten_meta_tags(meta))

            timestamp = entry.get("timestamp") or meta.get("timestamp") or time.time()
            tags.append(f"t:{float(timestamp)}")
            tags.append(f"a:{agent_id}")
            tags.append(f"x:{axis_id}")

            if entry.get("error_type"):
                tags.append(str(entry["error_type"]))

            project = table_name or entry.get("table_name") or "default"

            params = {
                "content": content,
                "tags": tags,
                "importance": float(entry.get("importance", 0.5)),
                "project": project,
                "session_id": entry.get("session_id", "default"),
            }

            session = self._get_session()
            session.call_tool_sync("remember", params)
            return True
        except Exception as e:
            logger.error(f"SLMClient.remember failed: {e}")
            return False

    async def ahealth(self) -> bool:
        if not _heartbeat.needs_refresh():
            return _heartbeat.healthy

        try:
            session = self._get_session()
            res = await session.call_tool_async("get_status", {})
            is_ok = isinstance(res, dict) and res.get("status") == "healthy"
            _heartbeat.update(is_ok)
            return is_ok
        except Exception:
            _heartbeat.update(False)
            return False

    async def asearch(
        self,
        query: str,
        limit: int = 5,
        table_name: str | None = None,
        session_id: str | None = None,
    ) -> list[dict]:
        project = table_name or "default"
        params = {"query": query, "limit": limit, "project": project}
        if session_id:
            params["session_id"] = session_id

        try:
            session = self._get_session()
            res = await session.call_tool_async("recall", params)
            raw_results = []
            if isinstance(res, dict):
                raw_results = res.get("results", [])
            elif isinstance(res, list):
                raw_results = res

            filtered = []
            for r in raw_results:
                norm = _normalize_result(r)
                if session_id:
                    if norm["session_id"] in (session_id, "system", "default", "global"):
                        filtered.append(norm)
                else:
                    filtered.append(norm)
            return filtered
        except Exception as e:
            logger.error(f"SLMClient.asearch failed: {e}")
            return []

    async def aremember(
        self,
        entry: dict,
        table_name: str | None = None,
        agent_id: str = "system",
        axis_id: int = 6,
    ) -> bool:
        try:
            content = entry.get("text") or entry.get("prevention_rule") or ""

            tags = []
            vector = entry.get("vector")
            if vector is not None:
                tags.append(f"v:{_serialize_vector(vector)}")

            meta = entry.get("metadata") or {}
            if isinstance(meta, dict):
                tags.extend(self._flatten_meta_tags(meta))

            timestamp = entry.get("timestamp") or meta.get("timestamp") or time.time()
            tags.append(f"t:{float(timestamp)}")
            tags.append(f"a:{agent_id}")
            tags.append(f"x:{axis_id}")

            if entry.get("error_type"):
                tags.append(str(entry["error_type"]))

            project = table_name or entry.get("table_name") or "default"

            params = {
                "content": content,
                "tags": tags,
                "importance": float(entry.get("importance", 0.5)),
                "project": project,
                "session_id": entry.get("session_id", "default"),
            }

            session = self._get_session()
            await session.call_tool_async("remember", params)
            return True
        except Exception as e:
            logger.error(f"SLMClient.aremember failed: {e}")
            return False

    def observe(self, content: str, agent_id: str = "system") -> bool:
        try:
            params = {"content": content, "agent_id": agent_id}
            session = self._get_session()
            session.call_tool_sync("observe", params)
            return True
        except Exception as e:
            logger.error(f"SLMClient.observe failed: {e}")
            return False

    async def aobserve(self, content: str, agent_id: str = "system") -> bool:
        try:
            params = {"content": content, "agent_id": agent_id}
            session = self._get_session()
            await session.call_tool_async("observe", params)
            return True
        except Exception as e:
            logger.error(f"SLMClient.aobserve failed: {e}")
            return False

    def import_entry(self, entry: dict, table_name: str | None = None) -> bool:
        return self.remember(entry, table_name=table_name)

    async def aimport_entry(self, entry: dict, table_name: str | None = None) -> bool:
        return await self.aremember(entry, table_name=table_name)

    def embed(self, text: str) -> list[float]:
        try:
            session = self._get_session()
            res = session.call_tool_sync("aembed", {"text": text})
            if isinstance(res, dict) and "embedding" in res:
                return res["embedding"]
            emb = res if isinstance(res, list) else []
            return emb
        except Exception as e:
            logger.error(f"SLMClient.embed failed: {e}")
            return []

    async def aembed(self, text: str) -> list[float]:
        try:
            session = self._get_session()
            res = await session.call_tool_async("aembed", {"text": text})
            if isinstance(res, dict) and "embedding" in res:
                return res["embedding"]
            emb = res if isinstance(res, list) else []
            return emb
        except Exception as e:
            logger.error(f"SLMClient.aembed failed: {e}")
            return []

    def rerank(self, query: str, documents: list[str], top_n: int = 3) -> dict:
        try:
            session = self._get_session()
            res = session.call_tool_sync(
                "rerank",
                {
                    "query": query,
                    "documents": documents,
                    "top_n": top_n,
                },
            )
            if isinstance(res, dict) and "results" in res:
                return res
            return {"results": []}
        except Exception as e:
            logger.error(f"SLMClient.rerank failed: {e}")
            return {"results": []}

    async def arerank(self, query: str, documents: list[str], top_n: int = 3) -> dict:
        try:
            session = self._get_session()
            res = await session.call_tool_async(
                "rerank",
                {
                    "query": query,
                    "documents": documents,
                    "top_n": top_n,
                },
            )
            if isinstance(res, dict) and "results" in res:
                return res
            return {"results": []}
        except Exception as e:
            logger.error(f"SLMClient.arerank failed: {e}")
            return {"results": []}


_client_instance = None


def get_slm_client() -> SLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = SLMClient()
    return _client_instance
