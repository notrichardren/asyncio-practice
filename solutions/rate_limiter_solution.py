from typing import Callable, Awaitable, TypeVar
import time
import asyncio
from collections import deque

T = TypeVar("T")

class RateLimiter:
    def __init__(self, operations_per_second: int):
        # Initialize the rate limiter with operations allowed per second
        if operations_per_second <= 0:
            raise ValueError
        
        self.operations_per_second = operations_per_second
        self.lock = asyncio.Lock()
        self.timestamps = deque()
        
    async def acquire(self) -> None:
        # Acquire permission to perform an operation
        # If the rate limit is exceeded, this coroutine should wait
        # until performing the operation would not exceed the rate limit
        while True:

            old_time = None

            async with self.lock:
                if len(self.timestamps) == self.operations_per_second: # full deque

                    old_time = self.timestamps.popleft()

                    if time.time() - old_time > 1: # see if timeout
                        self.timestamps.append(time.time())
                        return
                    else: # else hasn't timed out; put it back and check later
                        self.timestamps.appendleft(old_time)

                else:
                    self.timestamps.append(time.time())
                    return
            
            if old_time:
                await asyncio.sleep(old_time+1 - time.time()) # asyncio sleep works with negative values
        
    async def execute(self, coroutine_func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        # Execute a coroutine function with rate limiting
        # This method should:
        # 1. Acquire permission using self.acquire()
        # 2. Execute the provided coroutine function with the given arguments
        # 3. Return the result of the coroutine function
        await self.acquire()

        return await coroutine_func(*args, **kwargs)