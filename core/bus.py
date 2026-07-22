"""Async message bus for inter-agent communication."""
import asyncio
from collections import defaultdict
from typing import Callable, Optional


class Bus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _ensure_queue(self):
        if self._queue is None:
            self._queue = asyncio.Queue()

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Store the running event loop so sync threads can publish."""
        self._loop = loop

    def subscribe(self, topic: str, callback: Callable):
        self._subscribers[topic].append(callback)

    def publish_sync(self, topic: str, payload: dict):
        """Thread-safe publish from synchronous (non-async) code."""
        loop = self._loop
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.publish(topic, payload), loop)
        else:
            # Fallback: call sync subscribers directly
            for cb in self._subscribers.get(topic, []):
                if not asyncio.iscoroutinefunction(cb):
                    try:
                        cb(payload)
                    except Exception:
                        pass

    async def publish(self, topic: str, payload: dict):
        self._ensure_queue()
        for cb in self._subscribers.get(topic, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(payload))
                else:
                    cb(payload)
            except Exception as e:
                print(f"[Bus] Error in subscriber for {topic}: {e}")

    async def publish_and_wait(self, topic: str, payload: dict):
        """Publish and await all async subscribers."""
        tasks = []
        for cb in self._subscribers.get(topic, []):
            if asyncio.iscoroutinefunction(cb):
                tasks.append(asyncio.create_task(cb(payload)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


bus = Bus()
