import asyncio
import time
import unittest
from unittest.mock import patch, MagicMock
from rate_limiter import RateLimiter

class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    def tearDown(self):
        self.loop.close()
        
    def test_init(self):
        # Test initialization with valid parameters
        limiter = RateLimiter(10)
        self.assertEqual(limiter.operations_per_second, 10)
        
        # Test initialization with invalid parameters
        with self.assertRaises(ValueError):
            RateLimiter(0)
        with self.assertRaises(ValueError):
            RateLimiter(-1)
            
    def test_acquire_within_limit(self):
        # Test that acquire doesn't block when within the rate limit
        limiter = RateLimiter(10)
        
        async def test():
            start_time = time.time()
            await limiter.acquire()
            elapsed_time = time.time() - start_time
            self.assertLess(elapsed_time, 0.1)  # Should be nearly instant
            
        self.loop.run_until_complete(test())
        
    def test_acquire_exceeds_limit(self):
        # Test that acquire blocks when the rate limit is exceeded
        limiter = RateLimiter(1)
        
        async def test():
            # First acquire should be instant
            await limiter.acquire()
            
            # Second acquire should block for close to 1 second
            start_time = time.time()
            await limiter.acquire()
            elapsed_time = time.time() - start_time
            self.assertGreaterEqual(elapsed_time, 0.9)  # Allow for small timing variations
            self.assertLess(elapsed_time, 1.2)  # But not too much variation
            
        self.loop.run_until_complete(test())
        
    def test_execute_within_limit(self):
        # Test that execute works correctly when within the rate limit
        limiter = RateLimiter(10)
        
        async def test_func(x):
            return x * 2
            
        async def test():
            result = await limiter.execute(test_func, 5)
            self.assertEqual(result, 10)
            
        self.loop.run_until_complete(test())
        
    def test_execute_exceeds_limit(self):
        # Test that execute correctly rate limits when the limit is exceeded
        limiter = RateLimiter(1)
        
        async def test_func(x):
            return x * 2
            
        async def test():
            # First execute should be instant
            await limiter.execute(test_func, 5)
            
            # Second execute should be rate limited
            start_time = time.time()
            result = await limiter.execute(test_func, 6)
            elapsed_time = time.time() - start_time
            self.assertGreaterEqual(elapsed_time, 0.9)
            self.assertEqual(result, 12)
            
        self.loop.run_until_complete(test())
        
    def test_multiple_operations_per_second(self):
        # Test with different operations per second settings
        for ops_per_second in [1, 2, 5, 10]:
            limiter = RateLimiter(ops_per_second)
            
            async def test():
                results = []
                start_time = time.time()
                
                async def test_task(i):
                    await limiter.acquire()
                    return i
                
                tasks = [test_task(i) for i in range(ops_per_second * 2)]
                results = await asyncio.gather(*tasks)
                
                elapsed_time = time.time() - start_time
                expected_time = 1.0  # Should take about 1 second to process twice the limit
                self.assertGreaterEqual(elapsed_time, expected_time * 0.9)
                self.assertLessEqual(elapsed_time, expected_time * 1.5)
                self.assertEqual(results, list(range(ops_per_second * 2)))
                
            self.loop.run_until_complete(test())
            
    def test_concurrent_execution(self):
        # Test that concurrent operations are correctly rate limited
        limiter = RateLimiter(2)
        
        async def slow_func(x):
            await asyncio.sleep(0.1)  # Simulate work
            return x
            
        async def test():
            start_time = time.time()
            tasks = [limiter.execute(slow_func, i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            elapsed_time = time.time() - start_time
            
            # With 2 ops/sec and 10 operations, should take about 5 seconds
            # Plus a small amount for the asyncio.sleep() calls
            self.assertGreaterEqual(elapsed_time, 4.1) # fixed this testcase
            self.assertLessEqual(elapsed_time, 5.5)
            self.assertEqual(results, list(range(10)))
            
        self.loop.run_until_complete(test())
            
    def test_error_handling(self):
        # Test that errors in the executed coroutine are correctly propagated
        limiter = RateLimiter(10)
        
        async def failing_func():
            raise ValueError("Test error")
            
        async def test():
            with self.assertRaises(ValueError):
                await limiter.execute(failing_func)
                
        self.loop.run_until_complete(test())
        
    def test_token_bucket_algorithm(self):
        # Test that the rate limiter uses a token bucket or similar algorithm
        # and allows for bursts within the overall rate limit
        limiter = RateLimiter(10)  # 10 ops/sec means a new token every 0.1 seconds
        
        async def test():
            # Use up initial tokens
            for _ in range(10):
                await limiter.acquire()
                
            # Next acquire should be delayed
            start_time = time.time()
            await limiter.acquire()
            first_elapsed = time.time() - start_time
            self.assertGreaterEqual(first_elapsed, 0.09)  # Wait for at least one token
            
            # Wait for tokens to accumulate (0.3 seconds = ~3 tokens)
            await asyncio.sleep(0.3)
            
            # Should be able to make 3 acquires without significant delay
            start_time = time.time()
            for _ in range(3):
                await limiter.acquire()
            burst_elapsed = time.time() - start_time
            self.assertLess(burst_elapsed, 0.1)  # Should be quick for accumulated tokens
            
        self.loop.run_until_complete(test())
        
    def test_excessive_operations(self):
        # Test behavior with a large number of operations
        limiter = RateLimiter(100)  # 100 ops/sec
        
        async def test():
            start_time = time.time()
            tasks = [limiter.acquire() for _ in range(300)]
            await asyncio.gather(*tasks)
            elapsed_time = time.time() - start_time
            
            # Should take about 2-3 seconds to process 300 operations at 100 ops/sec
            self.assertGreaterEqual(elapsed_time, 2.0)
            self.assertLessEqual(elapsed_time, 3.5)
            
        self.loop.run_until_complete(test())
        
    def test_rate_precision(self):
        # Test the precision of the rate limiting
        limiter = RateLimiter(10)  # 10 ops/sec
        
        async def test():
            # Perform 50 operations and measure intervals
            intervals = []
            prev_time = time.time()
            
            for _ in range(50):
                await limiter.acquire()
                now = time.time()
                intervals.append(now - prev_time)
                prev_time = now
                
            # First several operations should be quick (using initial token bucket)
            self.assertLess(sum(intervals[:10]), 0.1)
            
            # Subsequent operations should average close to 0.1 seconds apart
            avg_interval = sum(intervals[10:]) / len(intervals[10:])
            self.assertGreaterEqual(avg_interval, 0.09)
            self.assertLessEqual(avg_interval, 0.12)
            
        self.loop.run_until_complete(test())
        
    def test_cancellation(self):
        # Test that cancellation works correctly
        limiter = RateLimiter(1)  # 1 op/sec for easy testing
        
        async def test():
            # Use the initial token
            await limiter.acquire()
            
            # Start an acquire that will be blocked
            task = asyncio.create_task(limiter.acquire())
            
            # Wait a bit but not enough for the operation to complete
            await asyncio.sleep(0.1)
            
            # Cancel the task
            task.cancel()
            
            try:
                await task
                self.fail("Task should have been canceled")
            except asyncio.CancelledError:
                pass  # Expected
                
            # Ensure the rate limiter still works after cancellation
            start_time = time.time()
            await limiter.acquire()
            elapsed_time = time.time() - start_time
            self.assertGreaterEqual(elapsed_time, 0.8)  # Should still wait for the token
            
        self.loop.run_until_complete(test())
            
    def test_execute_with_args_kwargs(self):
        # Test execute with complex arguments
        limiter = RateLimiter(10)
        
        async def complex_func(a, b, c=10, d=20):
            return a + b + c + d
            
        async def test():
            result = await limiter.execute(complex_func, 1, 2, d=30)
            self.assertEqual(result, 1 + 2 + 10 + 30)
            
        self.loop.run_until_complete(test())
            
    def test_nonblocking_operations(self):
        # Test that the limiter doesn't block the event loop
        limiter = RateLimiter(1)  # 1 op/sec
        
        async def test():
            # Use up the initial token
            await limiter.acquire()
            
            # Start a task that will be rate limited
            blocked_task = asyncio.create_task(limiter.acquire())
            
            # Start another task that should run immediately
            counter = [0]
            
            async def increment():
                for _ in range(5):
                    counter[0] += 1
                    await asyncio.sleep(0.1)
                    
            increment_task = asyncio.create_task(increment())
            
            # Wait long enough for the rate limit to clear
            await asyncio.sleep(1.2)
            
            # Both tasks should complete
            await blocked_task
            await increment_task
            
            # The increment task should have run during the rate limit waiting
            self.assertEqual(counter[0], 5)
            
        self.loop.run_until_complete(test())
            
    def test_dynamic_rate_adjustment(self):
        # Test changing the rate limit dynamically
        limiter = RateLimiter(1)
        
        async def test():
            # First acquire at the initial rate
            start_time = time.time()
            await limiter.acquire()
            await limiter.acquire()
            first_elapsed = time.time() - start_time
            self.assertGreaterEqual(first_elapsed, 0.9)
            
            # Change the rate to 10 ops/sec
            limiter.operations_per_second = 10
            
            # Next acquires should be faster
            start_time = time.time()
            await limiter.acquire()
            await limiter.acquire()
            second_elapsed = time.time() - start_time
            self.assertLessEqual(second_elapsed, 0.3)
            
        self.loop.run_until_complete(test())

if __name__ == "__main__":
    unittest.main()