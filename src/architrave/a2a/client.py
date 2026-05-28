from typing import Any

import httpx

from src.architrave.a2a.auth import sign_payload
from src.architrave.a2a.protocol import BusMessage, serialize_to_a2a
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


async def send_a2a_message(
    target_endpoint: str, msg: BusMessage, secret: str, sender_endpoint: str, timeout_s: float = 5.0
) -> dict[str, Any]:
    """
    Send a signed BusMessage to a remote agent endpoint using HTTP POST.
    """
    try:
        # Prepare wire payload and signature
        payload = serialize_to_a2a(msg, sender_endpoint)
        signature = sign_payload(payload, secret)

        headers = {"Content-Type": "application/json", "X-A2A-Signature": signature}

        # Clean URL to ensure valid route path
        endpoint_url = target_endpoint.rstrip("/")
        if not endpoint_url.endswith("/a2a/message"):
            endpoint_url = f"{endpoint_url}/a2a/message"

        logger.info(
            f"A2A Client: Sending signed message '{msg.id}' (topic: '{msg.topic}') to '{endpoint_url}'"
        )

        async with httpx.AsyncClient() as client:
            resp = await client.post(endpoint_url, json=payload, headers=headers, timeout=timeout_s)

            if resp.status_code == 200:
                logger.info(
                    f"A2A Client: Message '{msg.id}' successfully received by '{target_endpoint}'"
                )
                return resp.json()
            else:
                err_msg = f"HTTP status {resp.status_code}: {resp.text}"
                logger.error(f"A2A Client: Failed to deliver message '{msg.id}'. {err_msg}")
                return {"status": "error", "error": err_msg}

    except httpx.TimeoutException as te:
        logger.error(
            f"A2A Client: Timeout delivering message '{msg.id}' to '{target_endpoint}' ({te})"
        )
        return {"status": "error", "error": "A2ATimeoutError: Connection timed out after 5 seconds"}
    except Exception as e:
        logger.error(
            f"A2A Client: Unexpected exception delivering message '{msg.id}' to '{target_endpoint}' ({e})"
        )
        return {"status": "error", "error": f"A2AError: {e!s}"}
