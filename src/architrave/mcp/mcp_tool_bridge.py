import asyncio
from typing import Any

import numpy as np

from src.utils.logging_config import setup_logger

from .mcp_registry import get_mcp_registry

logger = setup_logger(__name__)


def make_remember_handler(srv_name: str, t_name: str, _mcp_sess: Any):
    async def handler(_self, input_data: Any):
        logger.info(
            f"ToolBridge: Intercepting and executing as async MCP tool '{srv_name}_{t_name}'"
        )
        kwargs = {}
        if isinstance(input_data, dict):
            kwargs = input_data
        elif input_data is not None:
            kwargs = {"content": str(input_data)}

        project = kwargs.get("project") or "default"
        session_id = kwargs.get("session_id") or "default"
        content = kwargs.get("content") or ""
        agent_id = kwargs.get("agent_id") or "system"
        axis_id = kwargs.get("axis_id", 6)
        if not isinstance(axis_id, int):
            try:
                axis_id = int(axis_id)
            except (ValueError, TypeError):
                axis_id = 6

        vector = kwargs.get("vector") or np.zeros(256)
        if isinstance(vector, list):
            vector = np.array(vector)

        metadata = kwargs.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {"raw_meta": metadata}
        metadata["session_id"] = session_id
        metadata["agent_id"] = agent_id
        metadata["axis_id"] = axis_id

        if project == "failure_memory":
            from cognition.mnemosyne.semantic_store import FailureMemoryStore

            fm_store = FailureMemoryStore()
            error_type = kwargs.get("error_type") or metadata.get("error_type") or "unknown"
            context_hash = kwargs.get("context_hash") or metadata.get("context_hash") or "unknown"
            await asyncio.to_thread(
                fm_store.add_failure_vector,
                prevention_rule=content,
                vector=vector,
                error_type=error_type,
                context_hash=context_hash,
                metadata=metadata,
            )
        else:
            from cognition.mnemosyne.semantic_store import SemanticStore

            sem_store = SemanticStore()
            await asyncio.to_thread(
                sem_store.add_memories,
                texts=[content],
                vectors=[vector],
                metadata=[metadata],
                session_id=session_id,
            )
        return {"status": "success"}

    return handler


def make_observe_handler(srv_name: str, t_name: str, _mcp_sess: Any):
    async def handler(self, input_data: Any):
        logger.info(
            f"ToolBridge: Intercepting and executing as async MCP tool '{srv_name}_{t_name}'"
        )
        kwargs = {}
        if isinstance(input_data, dict):
            kwargs = input_data
        elif input_data is not None:
            kwargs = {"content": str(input_data)}

        from src.architrave.mcp import get_slm_client

        slm = get_slm_client()
        content = kwargs.get("content") or ""
        agent_id = kwargs.get("agent_id") or self.agent_id
        await slm.aobserve(content=content, agent_id=agent_id)
        return {"status": "success"}

    return handler


def discover_and_register_mcp_tools(tool_bridge_cls: Any) -> None:
    """
    MCP Registry'deki tüm aktif sunucuların araçlarını sorgular ve
    ToolBridge sınıfına class-level olarak `{server_name}_{tool_name}` ön ekiyle kaydeder.
    """
    try:
        registry = get_mcp_registry()
        sessions = registry.get_all_sessions()

        discovered_count = 0
        for server_name, session in sessions.items():
            if not session.enabled:
                logger.info(
                    f"discover_and_register_mcp_tools: Skipping disabled server '{server_name}'"
                )
                continue

            logger.info(
                f"discover_and_register_mcp_tools: Discovering tools for server '{server_name}'..."
            )
            try:
                tools = session.list_tools_sync()
                for tool in tools:
                    tool_name = getattr(tool, "name", None) or tool.get("name")
                    if not tool_name:
                        continue

                    if server_name == "slm" and tool_name == "remember":
                        handler_func = make_remember_handler(server_name, tool_name, session)
                    elif server_name == "slm" and tool_name == "observe":
                        handler_func = make_observe_handler(server_name, tool_name, session)
                    else:

                        def make_handler(srv_name: str, t_name: str, mcp_sess: Any):
                            async def handler(_self, input_data: Any):
                                logger.info(
                                    f"ToolBridge: Dynamically executing MCP tool '{srv_name}_{t_name}'"
                                )
                                kwargs = {}
                                if isinstance(input_data, dict):
                                    kwargs = input_data
                                elif input_data is not None:
                                    kwargs = {"value": input_data}
                                return await mcp_sess.call_tool_async(t_name, kwargs)

                            return handler

                        handler_func = make_handler(server_name, tool_name, session)

                    # Register to ToolBridge class
                    tool_bridge_cls.register_mcp_tool(
                        server_name=server_name, tool_name=tool_name, handler=handler_func
                    )
                    discovered_count += 1
                    logger.info(
                        f"discover_and_register_mcp_tools: Registered dynamic tool '{server_name}_{tool_name}'"
                    )
            except Exception as e:
                logger.error(
                    f"discover_and_register_mcp_tools: Failed to list/register tools for '{server_name}': {e}"
                )

        logger.info(
            f"discover_and_register_mcp_tools: Discovered and registered {discovered_count} tools on ToolBridge class."
        )
    except Exception as e:
        logger.error(f"discover_and_register_mcp_tools: Failed entirely: {e}")
