"""
SLM Client -- HTTP transport only.

Communicates directly with the SLM daemon at http://localhost:8765.
MCP stdio approach removed: slm.exe mcp never responds to MCP JSON-RPC
initialize handshake, causing permanent 30-second timeouts per client.
Single HTTP daemon serves all concurrent clients without per-client subprocess.
"""

import asyncio
import base64
import contextlib
import http.client
import json
import struct
import threading
import time
import urllib.parse
from dataclasses import dataclass

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Heartbeat cache -- 15s TTL, 60s backoff after failure
# ---------------------------------------------------------------------------


class SLMHeartbeatCache:
    """Thread-safe health result cache. 15s TTL, 60s backoff on failure."""

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


# ---------------------------------------------------------------------------
# Serialization helpers -- used by remember() to encode structured metadata
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# HTTP response normalizer -- maps /recall item to canonical dict shape
# ---------------------------------------------------------------------------

_FACT_TYPE_AXIS: dict[str, int] = {
    "episodic": 1,
    "procedural": 2,
    "goal": 3,
    "temporal": 4,
    "spatial": 5,
    "semantic": 6,
    "operational": 7,
    "meta": 8,
    "metacognition": 8,
    "tone": 9,
    "rational": 10,
    "verification": 11,
    "efficiency": 12,
    "cross_session": 13,
    "visual": 14,
}


def _normalize_http_result(item: dict) -> dict:
    """Map a /recall HTTP response item to the canonical SLMClient result shape."""
    content = item.get("content") or item.get("source_content") or ""
    fact_type = (item.get("fact_type") or "semantic").lower()
    axis_id = _FACT_TYPE_AXIS.get(fact_type, 6)
    # confidence is already 0-1; clamp to guard against out-of-range server values
    importance = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
    context_hash = item.get("fact_id") or item.get("memory_id") or "unknown"

    return {
        "vector": [],
        "text": content,
        "prevention_rule": content,
        "session_id": "default",
        "metadata": json.dumps({}),
        "importance": importance,
        "timestamp": 0.0,
        "error_type": "unknown",
        "context_hash": context_hash,
        "agent_id": "system",
        "axis_id": axis_id,
    }


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class SLMConfig:
    http_port: int = 8765
    http_op_timeout: float = 30.0
    http_health_timeout: float = 5.0
    endpoint: str = "http://localhost:8081"  # legacy field kept for test compat


# ---------------------------------------------------------------------------
# HTTP transport (internal) -- uses http.client to avoid S310 (urllib audit)
# ---------------------------------------------------------------------------


class _SLMHttpTransport:
    """http.client wrapper for the SLM HTTP daemon. No external dependencies."""

    def __init__(
        self,
        port: int = 8765,
        op_timeout: float = 30.0,
        health_timeout: float = 5.0,
    ):
        self._host = "localhost"
        self._port = port
        self._op_timeout = op_timeout
        self._health_timeout = health_timeout

    def _conn(self, timeout: float) -> http.client.HTTPConnection:
        return http.client.HTTPConnection(self._host, self._port, timeout=timeout)

    def _get(self, path: str, params: dict | None = None, timeout: float | None = None) -> dict:
        if params:
            path += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        conn = self._conn(timeout or self._op_timeout)
        try:
            conn.request("GET", path)
            resp = conn.getresponse()
            return json.loads(resp.read().decode("utf-8"))
        finally:
            conn.close()

    def _post(self, path: str, body: dict, timeout: float | None = None) -> dict:
        data = json.dumps(body).encode("utf-8")
        conn = self._conn(timeout or self._op_timeout)
        try:
            conn.request(
                "POST",
                path,
                body=data,
                headers={"Content-Type": "application/json"},
            )
            resp = conn.getresponse()
            return json.loads(resp.read().decode("utf-8"))
        finally:
            conn.close()

    def health(self) -> bool:
        try:
            data = self._get("/health", timeout=self._health_timeout)
            return data.get("status") == "ok"
        except Exception:
            return False

    def search(
        self,
        query: str,
        limit: int = 5,
        project: str | None = None,
    ) -> list[dict]:
        params: dict = {"q": query, "limit": limit}
        if project and project != "default":
            params["project_name"] = project
        data = self._get("/recall", params)
        return data.get("results", [])

    def remember(
        self,
        content: str,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> dict:
        body: dict = {"content": content}
        if tags:
            # HTTP API expects tags as a single comma-separated string
            body["tags"] = ",".join(str(t) for t in tags)
        if metadata:
            body["metadata"] = metadata
        return self._post("/remember", body)

    def observe(self, content: str) -> dict:
        return self._post("/observe", {"content": content})


# ---------------------------------------------------------------------------
# SLMClient -- public API (same interface, http.client under the hood)
# ---------------------------------------------------------------------------


class SLMClient:
    def __init__(self, config: SLMConfig | None = None) -> None:
        self.config = config or SLMConfig()
        self._transport = _SLMHttpTransport(
            port=self.config.http_port,
            op_timeout=self.config.http_op_timeout,
            health_timeout=self.config.http_health_timeout,
        )

    # -- health --------------------------------------------------------------

    def health(self) -> bool:
        if not _heartbeat.needs_refresh():
            return _heartbeat.healthy
        result = self._transport.health()
        _heartbeat.update(result)
        return result

    async def ahealth(self) -> bool:
        if not _heartbeat.needs_refresh():
            return _heartbeat.healthy
        result = await asyncio.to_thread(self._transport.health)
        _heartbeat.update(result)
        return result

    # -- session_init (no-op over HTTP) -------------------------------------

    def session_init(self, project_path: str = "", query: str = "", max_results: int = 10) -> dict:
        return {}

    async def asession_init(
        self, project_path: str = "", query: str = "", max_results: int = 10
    ) -> dict:
        return {}

    # -- search / recall -----------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 5,
        table_name: str | None = None,
        session_id: str | None = None,
    ) -> list[dict]:
        project = table_name or "default"
        try:
            raw_results = self._transport.search(query, limit=limit, project=project)
            filtered = []
            for item in raw_results:
                norm = _normalize_http_result(item)
                if session_id:
                    if norm["session_id"] in (session_id, "system", "default", "global"):
                        filtered.append(norm)
                else:
                    filtered.append(norm)
            return filtered
        except Exception as e:
            logger.error(f"SLMClient.search failed: {e}")
            return []

    async def asearch(
        self,
        query: str,
        limit: int = 5,
        table_name: str | None = None,
        session_id: str | None = None,
    ) -> list[dict]:
        project = table_name or "default"
        try:
            raw_results = await asyncio.to_thread(self._transport.search, query, limit, project)
            filtered = []
            for item in raw_results:
                norm = _normalize_http_result(item)
                if session_id:
                    if norm["session_id"] in (session_id, "system", "default", "global"):
                        filtered.append(norm)
                else:
                    filtered.append(norm)
            return filtered
        except Exception as e:
            logger.error(f"SLMClient.asearch failed: {e}")
            return []

    # -- remember ------------------------------------------------------------

    def remember(
        self,
        entry: dict,
        table_name: str | None = None,
        agent_id: str = "system",
        axis_id: int = 6,
    ) -> bool:
        try:
            content = entry.get("text") or entry.get("prevention_rule") or ""

            tags: list[str] = []
            vector = entry.get("vector")
            if vector is not None:
                tags.append(f"v:{_serialize_vector(vector)}")

            meta = entry.get("metadata") or {}
            if isinstance(meta, str):
                with contextlib.suppress(Exception):
                    meta = json.loads(meta)
            if isinstance(meta, dict):
                tags.extend(_flatten_meta_tags(meta))

            timestamp = (
                entry.get("timestamp")
                or (meta.get("timestamp") if isinstance(meta, dict) else None)
                or time.time()
            )
            tags.append(f"t:{float(timestamp)}")
            tags.append(f"a:{agent_id}")
            tags.append(f"x:{axis_id}")

            if entry.get("error_type"):
                tags.append(str(entry["error_type"]))

            metadata_dict: dict = {}
            if isinstance(meta, dict):
                metadata_dict.update(meta)
            metadata_dict["project"] = table_name or entry.get("table_name") or "default"
            metadata_dict["session_id"] = entry.get("session_id", "default")
            metadata_dict["importance"] = float(entry.get("importance", 0.5))

            self._transport.remember(content, tags=tags, metadata=metadata_dict)
            return True
        except Exception as e:
            logger.error(f"SLMClient.remember failed: {e}")
            return False

    async def aremember(
        self,
        entry: dict,
        table_name: str | None = None,
        agent_id: str = "system",
        axis_id: int = 6,
    ) -> bool:
        try:
            content = entry.get("text") or entry.get("prevention_rule") or ""

            tags: list[str] = []
            vector = entry.get("vector")
            if vector is not None:
                tags.append(f"v:{_serialize_vector(vector)}")

            meta = entry.get("metadata") or {}
            if isinstance(meta, str):
                with contextlib.suppress(Exception):
                    meta = json.loads(meta)
            if isinstance(meta, dict):
                tags.extend(_flatten_meta_tags(meta))

            timestamp = (
                entry.get("timestamp")
                or (meta.get("timestamp") if isinstance(meta, dict) else None)
                or time.time()
            )
            tags.append(f"t:{float(timestamp)}")
            tags.append(f"a:{agent_id}")
            tags.append(f"x:{axis_id}")

            if entry.get("error_type"):
                tags.append(str(entry["error_type"]))

            metadata_dict: dict = {}
            if isinstance(meta, dict):
                metadata_dict.update(meta)
            metadata_dict["project"] = table_name or entry.get("table_name") or "default"
            metadata_dict["session_id"] = entry.get("session_id", "default")
            metadata_dict["importance"] = float(entry.get("importance", 0.5))

            await asyncio.to_thread(self._transport.remember, content, tags, metadata_dict)
            return True
        except Exception as e:
            logger.error(f"SLMClient.aremember failed: {e}")
            return False

    # -- import_entry (alias) ------------------------------------------------

    def import_entry(self, entry: dict, table_name: str | None = None) -> bool:
        return self.remember(entry, table_name=table_name)

    async def aimport_entry(self, entry: dict, table_name: str | None = None) -> bool:
        return await self.aremember(entry, table_name=table_name)

    # -- observe -------------------------------------------------------------

    def observe(self, content: str, agent_id: str = "system") -> bool:
        try:
            self._transport.observe(content)
            return True
        except Exception as e:
            logger.error(f"SLMClient.observe failed: {e}")
            return False

    async def aobserve(self, content: str, agent_id: str = "system") -> bool:
        try:
            await asyncio.to_thread(self._transport.observe, content)
            return True
        except Exception as e:
            logger.error(f"SLMClient.aobserve failed: {e}")
            return False

    # -- embed (delegated to local Ollama by callers) ------------------------

    def embed(self, text: str) -> list[float]:
        # SLM HTTP daemon has no public embed endpoint.
        # All callers (matryoshka_service, theoria) gate on `if vec:` and
        # fall back to local Ollama -- returning [] triggers that path.
        logger.debug("SLMClient.embed: no HTTP endpoint, caller falls back to local Ollama")
        return []

    async def aembed(self, text: str) -> list[float]:
        logger.debug("SLMClient.aembed: no HTTP endpoint, caller falls back to local Ollama")
        return []

    # -- rerank (delegated to JinaReranker by callers) ----------------------

    def rerank(self, query: str, documents: list[str], top_n: int = 3) -> dict:
        # SLM HTTP daemon has no public rerank endpoint.
        # All callers (retrieval, kathedra) gate on results["results"] and
        # fall back to JinaReranker -- returning {"results":[]} triggers that.
        logger.debug("SLMClient.rerank: no HTTP endpoint, caller falls back to JinaReranker")
        return {"results": []}

    async def arerank(self, query: str, documents: list[str], top_n: int = 3) -> dict:
        logger.debug("SLMClient.arerank: no HTTP endpoint, caller falls back to JinaReranker")
        return {"results": []}


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_client_instance: SLMClient | None = None


def get_slm_client() -> SLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = SLMClient()
    return _client_instance
