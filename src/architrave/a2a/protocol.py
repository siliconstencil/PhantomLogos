import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BusMessage:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = "unknown"
    recipient: str = "broadcast"
    topic: str = "general"
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


PROTOCOL_VERSION = "1.0"


def serialize_to_a2a(msg: BusMessage, sender_endpoint: str) -> dict[str, Any]:
    """
    Serialize a BusMessage to the A2A wire JSON format.
    """
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_id": msg.id,
        "sender": {"agent_id": msg.sender, "endpoint": sender_endpoint},
        "recipient": msg.recipient,
        "topic": msg.topic,
        "payload": msg.payload,
        "timestamp": msg.timestamp,
    }


def deserialize_from_a2a(payload: dict[str, Any]) -> BusMessage:
    """
    Deserialize A2A wire JSON format to a BusMessage, preserving endpoint in metadata.
    """
    # Extract metadata details
    sender_info = payload.get("sender", {})
    agent_id = sender_info.get("agent_id", "unknown")
    sender_endpoint = sender_info.get("endpoint", "")

    # Retrieve other fields with default fallback
    msg_id = payload.get("message_id", "")
    recipient = payload.get("recipient", "broadcast")
    topic = payload.get("topic", "general")
    msg_payload = payload.get("payload", {})
    timestamp = payload.get("timestamp", 0.0)

    # Initialize BusMessage. Since state_bus.py is modified to support metadata,
    # we construct it and attach metadata dictionary.
    msg = BusMessage(
        id=msg_id,
        sender=agent_id,
        recipient=recipient,
        topic=topic,
        payload=msg_payload,
        timestamp=timestamp,
    )
    # Store sender_endpoint under msg.metadata
    if not hasattr(msg, "metadata") or msg.metadata is None:
        msg.metadata = {}
    msg.metadata["sender_endpoint"] = sender_endpoint

    return msg
