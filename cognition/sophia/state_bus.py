import asyncio
import time
import uuid
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from src.utils.logging_config import setup_logger

import threading
logger = setup_logger(__name__)


@dataclass
class BusMessage:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = "unknown"
    recipient: str = "broadcast"
    topic: str = "general"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class StateBus:
    """
    Multi-agent asynchronous message queue.
    Enables agent-to-agent communication without tight coupling.
    """
    def __init__(self, max_size: int = 100):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._subscribers: Dict[str, list] = {}
        self._history: list = []

    async def publish(self, msg: BusMessage):
        await self._queue.put(msg)
        self._history.append(msg)
        if len(self._history) > 500:
            self._history = self._history[-200:]

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
                        logger.warning(f"Sophia: StateBus handler for {agent_id} cancelled mid-execution.")
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


_GLOBAL_BUS: Optional[StateBus] = None
_init_lock = threading.Lock()


def get_state_bus() -> StateBus:
    global _GLOBAL_BUS
    with _init_lock:
        if _GLOBAL_BUS is None:
            _GLOBAL_BUS = StateBus()
    return _GLOBAL_BUS
