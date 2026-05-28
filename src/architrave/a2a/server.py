import asyncio
import json
import os
import threading
import time

from aiohttp import web

from cognition.sophia.state_bus import get_state_bus
from src.architrave.a2a.auth import get_a2a_secret, verify_signature
from src.architrave.a2a.protocol import deserialize_from_a2a
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class A2AServer:
    def __init__(self, agent_id: str = "sophia", default_port: int = 32554) -> None:
        self.agent_id = agent_id
        self.default_port = default_port
        self.port = default_port
        self.host = "127.0.0.1"
        self._app = web.Application()
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._state_bus = get_state_bus()
        self._start_time = time.time()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

        # Set up routes
        self._app.router.add_post("/a2a/message", self.handle_message)
        self._app.router.add_get("/a2a/health", self.handle_health)

    async def handle_health(self, _request: web.Request) -> web.Response:
        """
        GET /a2a/health
        Health check endpoint.
        """
        uptime = time.time() - self._start_time
        data = {"agent_id": self.agent_id, "status": "alive", "uptime": int(uptime)}
        return web.json_response(data)

    async def handle_message(self, request: web.Request) -> web.Response:
        """
        POST /a2a/message
        Receives signed messages from remote agents.
        """
        try:
            signature = request.headers.get("X-A2A-Signature", "")
            if not signature:
                logger.warning(
                    "A2A Server: Received message request missing X-A2A-Signature header."
                )
                # Axis 8 (Failure log mapping placeholder)
                return web.json_response(
                    {"status": "error", "error": "Missing signature header"}, status=401
                )

            payload = await request.json()

            # Extract sender agent id to verify signature
            sender_info = payload.get("sender", {})
            sender_id = sender_info.get("agent_id", "unknown")

            secret = get_a2a_secret(sender_id)
            if not verify_signature(payload, secret, signature):
                logger.warning(
                    f"A2A Server: Invalid HMAC signature for message from sender '{sender_id}'."
                )
                # Record to failures/Axis 8 could be triggered here or logged.
                return web.json_response(
                    {"status": "error", "error": "Invalid signature"}, status=401
                )

            # Deserialize to BusMessage
            msg = deserialize_from_a2a(payload)

            # Thread-safe publishing: put directly to queue or use loop.call_soon if loop is active
            logger.info(
                f"A2A Server: Successfully validated message '{msg.id}' from '{sender_id}'. Publishing to StateBus."
            )

            # Since CPython's list.append and collections.deque.append (internals of asyncio.Queue)
            # are atomic and protected by the GIL, put_nowait from another thread is stable.
            # However, to trigger future wakeups correctly, we call loop.call_soon_threadsafe if possible.
            try:
                self._state_bus._queue.put_nowait(msg)
                self._state_bus._history.append(msg)
                if len(self._state_bus._history) > 500:
                    self._state_bus._history = self._state_bus._history[-200:]
            except Exception as e:
                logger.error(
                    f"A2A Server: Failed to publish message directly to StateBus queue ({e}). Trying fallback."
                )
                # Fallback send
                self._state_bus.send(msg.sender, msg.topic, msg.payload, msg.recipient)

            return web.json_response({"status": "ok", "message_id": msg.id})

        except json.JSONDecodeError:
            logger.error("A2A Server: Received request payload with invalid JSON format.")
            return web.json_response(
                {"status": "error", "error": "Invalid JSON format"}, status=400
            )
        except Exception as e:
            logger.error(f"A2A Server: Unexpected error handling A2A message request ({e})")
            return web.json_response({"status": "error", "error": str(e)}, status=500)

    async def _start_async(self, port: int) -> bool:
        """
        Internal async starter attempting to bind to a specific port.
        Supports port collision fallback by incrementing port.
        """
        current_port = port
        max_attempts = 10
        reserved_ports = {32556}  # FastAPI Sovereign Middleware
        for _attempt in range(max_attempts):
            if current_port in reserved_ports:
                current_port += 1
                continue
            try:
                self._runner = web.AppRunner(self._app)
                await self._runner.setup()
                self._site = web.TCPSite(self._runner, self.host, current_port)
                await self._site.start()
                self.port = current_port
                logger.info(f"A2A Server: Successfully started on {self.host}:{self.port}")

                # Single-time write update of own port in agent/a2a_registry.json
                self._update_registry_port()
                return True
            except OSError as e:
                if e.errno == 10048 or "already in use" in str(e).lower() or e.errno == 98:
                    logger.warning(
                        f"A2A Server: Port {current_port} is already in use. Retrying next port..."
                    )
                    current_port += 1
                else:
                    logger.error(
                        f"A2A Server: Failed to bind to port {current_port} due to socket error ({e})"
                    )
                    break
            except Exception as e:
                logger.error(f"A2A Server: Failed to setup runner/site ({e})")
                break
        return False

    def _update_registry_port(self) -> None:
        """
        Scan and update this agent's endpoint port inside agent/a2a_registry.json.
        """
        registry_path = os.path.join("agent", "a2a_registry.json")
        if not os.path.exists(registry_path):
            os.makedirs(os.path.dirname(registry_path), exist_ok=True)
            empty_reg = {"agents": []}
            with open(registry_path, "w") as f:
                json.dump(empty_reg, f, indent=2)

        try:
            with open(registry_path) as f:
                data = json.load(f)

            updated = False
            for agent in data.get("agents", []):
                if agent.get("agent_id") == self.agent_id:
                    # Update endpoint port
                    endpoint = agent.get("endpoint", "")
                    if endpoint:
                        # Reconstruct port
                        prefix = endpoint.rsplit(":", 1)[0]
                        agent["endpoint"] = f"{prefix}:{self.port}/a2a"
                        updated = True

            if not updated:
                # Add self as a new entry if not existing
                self_entry = {
                    "agent_id": self.agent_id,
                    "name": f"{self.agent_id.capitalize()} Agent",
                    "endpoint": f"http://127.0.0.1:{self.port}/a2a",
                    "capabilities": ["core", "orchestration"],
                    "skills": [],
                    "status": "online",
                    "last_heartbeat": time.time(),
                }
                if "agents" not in data:
                    data["agents"] = []
                data["agents"].append(self_entry)

            with open(registry_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(
                f"A2A Server: Updated registry file '{registry_path}' with active endpoint port '{self.port}'."
            )
        except Exception as e:
            logger.warning(
                f"A2A Server: Failed to update local registry with port {self.port} ({e})"
            )

    def start(self) -> None:
        """
        Starts the A2A server in a dedicated daemon thread with its own event loop.
        0 blocking risk for synchronous bootstrap daemon.
        """
        if self._thread and self._thread.is_alive():
            logger.info("A2A Server: Daemon thread is already running.")
            return

        def run_loop() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            def _exception_handler(_loop, context) -> None:
                msg = context.get("message", "")
                exc = context.get("exception", None)
                if exc and isinstance(exc, OSError) and "995" in str(exc):
                    return
                logger.warning(f"A2A Server: Unhandled event loop exception ({msg})")

            self._loop.set_exception_handler(_exception_handler)

            # Start the server asynchronously within our new loop
            started = self._loop.run_until_complete(self._start_async(self.default_port))
            if not started:
                logger.error("A2A Server: Failed to start web application in daemon loop.")
                return

            try:
                # Keep the loop running until stopped
                self._loop.run_forever()
            except Exception as e:
                logger.error(f"A2A Server: Event loop encountered exception ({e})")
            finally:
                logger.info("A2A Server: Daemon event loop is shutting down.")

        self._thread = threading.Thread(target=run_loop, name="A2ADaemonServer", daemon=True)
        self._thread.start()
        logger.info("A2A Server: Daemon thread spawned successfully.")

    async def stop(self) -> None:
        """
        Asynchronously clean up server runners, sites, and stop the event loop.
        """
        logger.info("A2A Server: Stopping web server...")
        try:
            if self._site:
                await self._site.stop()
            if self._runner:
                await self._runner.cleanup()
            logger.info("A2A Server: HTTP resources cleaned up successfully.")
        except Exception as e:
            logger.error(f"A2A Server: Exception during shutdown cleanup ({e})")
        finally:
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
