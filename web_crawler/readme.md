# Web Crawler with Dependency Resolution

## Problem Statement
Implement an asynchronous web crawler that can handle page dependencies. The crawler should visit web pages in an order that respects their dependencies, while maintaining a limit on the number of concurrent requests.

## Difficulty: Medium
This exercise tests your understanding of:
- Async/await patterns
- Task management and scheduling
- Dependency resolution
- Concurrency control
- Error handling in async contexts

## Requirements

```python
import asyncio
import random
from typing import Dict, List, Optional

async def fetch_page(url: str) -> str:
    """
    Simulated function to fetch a web page.
    In a real application, this would make an HTTP request.
    For this exercise, it simply returns a string with the page content.
    """
    await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate network latency
    return f"Content of {url}"

class WebCrawler:
    def __init__(self, max_concurrent_requests: int = 5):
        """
        Initialize the crawler with a limit on concurrent requests.
        
        Args:
            max_concurrent_requests: Maximum number of concurrent requests the crawler can make
        """
        pass
        
    async def add_url(self, url: str, dependencies: List[str] = None) -> None:
        """
        Add a URL to be crawled, with optional dependencies.
        The URL will not be crawled until all its dependencies have been crawled.
        
        Args:
            url: The URL to crawl
            dependencies: List of URLs that must be crawled before this URL
        """
        pass
        
    async def crawl(self) -> Dict[str, str]:
        """
        Crawl all added URLs, respecting dependencies and concurrency limits.
        
        Returns:
            A dictionary mapping URLs to their page content
        """
        pass
```

## Example Usage

```python
import asyncio
from web_crawler import WebCrawler, fetch_page

async def main():
    crawler = WebCrawler(max_concurrent_requests=2)
    
    # Add URLs with dependencies
    await crawler.add_url("https://example.com/page1")
    await crawler.add_url("https://example.com/page2", ["https://example.com/page1"])
    await crawler.add_url("https://example.com/page3", ["https://example.com/page2"])
    await crawler.add_url("https://example.com/page4")
    await crawler.add_url("https://example.com/page5", ["https://example.com/page1", "https://example.com/page4"])
    
    # Start crawling
    results = await crawler.crawl()
    
    # Print results
    for url, content in results.items():
        print(f"URL: {url}, Content length: {len(content)}")
    
asyncio.run(main())
```

## Expected Output
```
URL: https://example.com/page1, Content length: 33
URL: https://example.com/page4, Content length: 33
URL: https://example.com/page2, Content length: 33
URL: https://example.com/page5, Content length: 33
URL: https://example.com/page3, Content length: 33
```

Note: The exact order might vary due to the simulated network latency, but the dependencies must be respected.

## Constraints
- The crawler should respect the maximum concurrent requests limit
- The crawler should respect page dependencies
- The crawler should handle circular dependencies gracefully (detect and raise an error)
- The implementation should be efficient and not use busy-waiting
- The crawler should handle errors in fetching pages gracefully

## Key Concepts to Master
1. **Async Task Management**
   - Creating and managing multiple async tasks
   - Handling task dependencies
   - Controlling concurrent execution

2. **Dependency Resolution**
   - Graph traversal algorithms
   - Cycle detection
   - Topological sorting

3. **Concurrency Control**
   - Semaphores for limiting concurrent requests
   - Task synchronization
   - Resource management

4. **Error Handling**
   - Graceful failure handling
   - Task cancellation
   - Exception propagation

## Common Pitfalls to Avoid
1. Deadlocks in dependency resolution
2. Memory leaks from uncompleted tasks
3. Inefficient busy-waiting
4. Poor error handling
5. Race conditions in concurrent execution

## Test Cases
Your implementation should handle:
1. Basic dependency resolution
2. Circular dependencies
3. Concurrent request limiting
4. Error handling in page fetching
5. Empty dependency lists
6. Large dependency graphs
7. Task cancellation
8. Resource cleanup