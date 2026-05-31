"""
Phase 6 — Pattern 22: Redis Pub/Sub Production Mailboxes
Replaces JSONL file mailboxes with Redis Streams for distributed agent fleets.

Requires:  pip install redis
           A running Redis instance (default: localhost:6379)
           Or: docker run -p 6379:6379 redis
"""
import json
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Callable, Awaitable

try:
    import redis.asyncio as aioredis
except ImportError:
    raise ImportError("Run: pip install redis")


class RedisAgentMailbox:
    """
    Production mailbox backed by Redis Streams (XADD / XREADGROUP / XACK).

    Why Redis Streams over JSONL files:
    - Cross-machine: agents on different servers share one broker
    - Push delivery: no polling, sub-millisecond latency
    - Exactly-once: consumer groups guarantee each message processed once
    - Durable: messages persist in Redis even if consumers restart
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._client = await aioredis.from_url(
            self.redis_url, decode_responses=True
        )
        print(f"[Redis] Connected to {self.redis_url}")

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()

    def _stream_key(self, agent: str) -> str:
        return f"agent:mailbox:{agent}"

    def _group(self, agent: str) -> str:
        return f"consumers:{agent}"

    async def _ensure_stream(self, agent: str) -> None:
        """Create stream + consumer group if they don't exist."""
        try:
            await self._client.xgroup_create(
                self._stream_key(agent),
                self._group(agent),
                id="0",
                mkstream=True,
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def send(
        self,
        to_agent: str,
        from_agent: str,
        message: dict,
    ) -> str:
        """
        Send a message to an agent's stream.
        Returns the Redis stream entry ID.
        """
        await self._ensure_stream(to_agent)
        envelope = {
            "id":        str(uuid.uuid4()),
            "from":      from_agent,
            "to":        to_agent,
            "timestamp": datetime.utcnow().isoformat(),
            "payload":   json.dumps(message),
        }
        msg_id = await self._client.xadd(self._stream_key(to_agent), envelope)
        return msg_id

    async def receive(
        self,
        agent_name: str,
        consumer_id: str,
        count: int = 10,
        block_ms: int = 2000,
    ) -> list[tuple[str, dict]]:
        """
        Read undelivered messages for this consumer.
        Blocks up to block_ms ms if the stream is empty.
        Returns list of (redis_msg_id, envelope) tuples.
        """
        await self._ensure_stream(agent_name)
        results = await self._client.xreadgroup(
            groupname=self._group(agent_name),
            consumername=consumer_id,
            streams={self._stream_key(agent_name): ">"},
            count=count,
            block=block_ms,
        )
        messages = []
        if results:
            for _, entries in results:
                for msg_id, fields in entries:
                    envelope = {**fields, "payload": json.loads(fields["payload"])}
                    messages.append((msg_id, envelope))
        return messages

    async def acknowledge(self, agent_name: str, msg_id: str) -> None:
        """Mark a message as successfully processed."""
        await self._client.xack(
            self._stream_key(agent_name),
            self._group(agent_name),
            msg_id,
        )

    async def agent_loop(
        self,
        agent_name: str,
        consumer_id: str,
        handler: Callable[[str, dict], Awaitable[None]],
        max_iterations: Optional[int] = None,
    ) -> None:
        """
        Run a continuous receive-process-acknowledge loop.

        handler(from_agent, payload) is called for each message.
        On success the message is acknowledged; on error it is NOT
        acknowledged so Redis will redeliver it.
        """
        print(f"[{agent_name}/{consumer_id}] Listening on Redis stream...")
        iterations = 0

        while max_iterations is None or iterations < max_iterations:
            messages = await self.receive(agent_name, consumer_id)
            for msg_id, envelope in messages:
                try:
                    await handler(envelope["from"], envelope["payload"])
                    await self.acknowledge(agent_name, msg_id)
                except Exception as e:
                    print(f"[{agent_name}] Error handling {msg_id}: {e} — will retry")
            iterations += 1


# ── Example: coordinator → reviewer workflow ──────────────────────────────────
async def demo():
    mailbox = RedisAgentMailbox()
    await mailbox.connect()

    # Coordinator sends a review request
    msg_id = await mailbox.send(
        to_agent="reviewer",
        from_agent="coordinator",
        message={"type": "review_request", "file": "src/auth.py"},
    )
    print(f"Sent: {msg_id}")

    # Reviewer processes its inbox (one iteration)
    async def handle(from_agent: str, payload: dict):
        print(f"Reviewer got from {from_agent}: {payload}")
        await mailbox.send(
            to_agent=from_agent,
            from_agent="reviewer",
            message={"type": "review_done", "result": "LGTM"},
        )

    await mailbox.agent_loop("reviewer", "reviewer-1", handle, max_iterations=1)

    # Coordinator reads the reply
    async def handle_reply(from_agent: str, payload: dict):
        print(f"Coordinator got reply from {from_agent}: {payload}")

    await mailbox.agent_loop("coordinator", "coord-1", handle_reply, max_iterations=1)

    await mailbox.disconnect()


if __name__ == "__main__":
    asyncio.run(demo())
