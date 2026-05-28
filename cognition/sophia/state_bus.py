import asyncio
import threading
from collections.abc import Awaitable, Callable

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


from src.architrave.a2a.protocol import BusMessage


class StateBus:
    """
    Multi-agent asynchronous message queue.
    Enables agent-to-agent communication without tight coupling.
    """

    def __init__(self, max_size: int = 100):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._subscribers: dict[str, list] = {}
        self._history: list = []

    async def publish(self, msg: BusMessage):
        try:
            from src.architrave.a2a.discovery import A2ADiscovery

            discovery = A2ADiscovery()
            remote_agent = discovery.resolve(msg.recipient)
        except Exception as e:
            logger.warning(
                f"Sophia: StateBus could not resolve remote discovery ({e}). Treating as local."
            )
            remote_agent = None

        is_remote = remote_agent is not None
        is_broadcast = msg.recipient == "broadcast"

        # Check if recipient is local agent
        if is_broadcast or not is_remote:
            await self._queue.put(msg)
            self._history.append(msg)
            if len(self._history) > 500:
                self._history = self._history[-200:]

        # Handle Remote Routing
        if is_broadcast:
            # Parallel remote publish to all online remote agents
            try:
                online_agents = discovery.list_online_agents()
                for agent in online_agents:
                    if agent.agent_id != msg.sender:  # avoid sending back to sender
                        asyncio.create_task(self._send_remote_safe(agent, msg, discovery))
            except Exception as e:
                logger.error(f"Sophia: Failed to broadcast to remote agents ({e})")
        elif is_remote:
            self._history.append(msg)
            if len(self._history) > 500:
                self._history = self._history[-200:]

            success = await self._send_remote_safe(remote_agent, msg, discovery)
            if not success:
                logger.warning(
                    f"Sophia: Remote delivery failed for '{msg.recipient}'. Performing local fallback."
                )
                await self._queue.put(msg)

    async def _send_remote_safe(self, remote_agent, msg: BusMessage, discovery) -> bool:
        try:
            from src.architrave.a2a.auth import get_a2a_secret
            from src.architrave.a2a.client import send_a2a_message

            local_id = msg.sender if msg.sender and msg.sender != "unknown" else "sophia"
            secret = get_a2a_secret(local_id)
            local_agent = discovery.resolve(local_id)
            sender_endpoint = local_agent.endpoint if local_agent else "http://127.0.0.1:32554/a2a"

            res = await send_a2a_message(
                target_endpoint=remote_agent.endpoint,
                msg=msg,
                secret=secret,
                sender_endpoint=sender_endpoint,
                timeout_s=5.0,
            )

            if res.get("status") == "ok":
                logger.info(
                    f"Sophia: Successfully routed message '{msg.id}' to remote agent '{remote_agent.agent_id}' [SRC:axis_1]"
                )
                return True
            else:
                logger.error(
                    f"Sophia: A2A remote send failed. Error: {res.get('error')} [SRC:axis_8]"
                )
                return False
        except Exception as e:
            logger.error(
                f"Sophia: Exception sending message '{msg.id}' to remote '{remote_agent.agent_id}' ({e}) [SRC:axis_8]"
            )
            return False

    def subscribe(self, agent_id: str, handler: Callable[[BusMessage], Awaitable[None]]):
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        self._subscribers[agent_id].append(handler)

    async def start_listener(self, agent_id: str):
        while True:
            try:
                msg = await self._queue.get()
            except asyncio.CancelledError:
                logger.info(f"Sophia: StateBus listener for {agent_id} cancelled. Shutting down.")
                break
            if msg.recipient in (agent_id, "broadcast"):
                handlers = self._subscribers.get(agent_id, [])
                for handler in handlers:
                    try:
                        await handler(msg)
                    except asyncio.CancelledError:
                        logger.warning(
                            f"Sophia: StateBus handler for {agent_id} cancelled mid-execution."
                        )
                        break
                    except Exception as e:
                        logger.error(f"Sophia: StateBus handler failed for {agent_id} ({e})")
            self._queue.task_done()

    def recent(self, limit: int = 10):
        return self._history[-limit:]

    def send(self, sender: str, topic: str, payload: dict, recipient: str = "broadcast"):
        msg = BusMessage(sender=sender, recipient=recipient, topic=topic, payload=payload)
        try:
            self._queue.put_nowait(msg)
            self._history.append(msg)
        except asyncio.QueueFull:
            logger.warning(f"Sophia: StateBus queue full, message from {sender} dropped.")


_GLOBAL_BUS: StateBus | None = None
_init_lock = threading.Lock()


def get_state_bus() -> StateBus:
    global _GLOBAL_BUS
    with _init_lock:
        if _GLOBAL_BUS is None:
            _GLOBAL_BUS = StateBus()
    return _GLOBAL_BUS
