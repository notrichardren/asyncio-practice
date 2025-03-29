import asyncio
import random
from typing import Dict, List, Optional
from collections import defaultdict

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
        if max_concurrent_requests <= 0:
            raise ValueError
        
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.processed_urls = set()

        self.out_neighbors = defaultdict(list)
        self.in_degree = {}

        self.lock = asyncio.Lock()
        
    async def add_url(self, url: str, dependencies: List[str] = None) -> None:
        """
        Add a URL to be crawled, with optional dependencies.
        The URL will not be crawled until all its dependencies have been crawled.
        
        Args:
            url: The URL to crawl
            dependencies: List of URLs that must be crawled before this URL
        """

        async with self.lock:
            # Initialize the URL if it doesn't exist
            if url not in self.in_degree:
                self.in_degree[url] = 0
                
            if dependencies:
                for dependency in dependencies:
                    # Initialize the dependency if it doesn't exist
                    if dependency not in self.in_degree:
                        self.in_degree[dependency] = 0
                        
                    self.out_neighbors[dependency].append(url)
                    self.in_degree[url] += 1
        
    async def crawl(self) -> Dict[str, str]:
        """
        Crawl all added URLs, respecting dependencies and concurrency limits.
        
        Returns:
            A dictionary mapping URLs to their page content
        """

        q = asyncio.Queue()
        results = {}

        # Add URLs with in-degree 0 to the queue
        initial_count = 0
        for url, num in self.in_degree.items():
            if num == 0:
                await q.put(url)
                initial_count += 1

        # If queue is empty from the start and we have URLs, we have a cycle
        if initial_count == 0 and self.in_degree:
            raise ValueError("Dependency cycle detected")

        async def crawl_worker():

            while True:
                url = await q.get()
                # print(f"we're processing {url}")

                async with self.lock:
                    self.processed_urls.add(url)

                if url is None:
                    q.task_done()
                    break

                for neighbor in self.out_neighbors[url]:
                    async with self.lock:
                        self.in_degree[neighbor] -= 1
                        if self.in_degree[neighbor] == 0 and neighbor not in self.processed_urls:
                            # print(f"we put in {neighbor} into the queue")
                            await q.put(neighbor)

                # async with self.semaphore:
                try:
                    result = await fetch_page(url)
                except Exception:
                    result = "ERROR"

                async with self.lock:
                    results[url] = result

                # print(f"done with {url}")

                q.task_done()

        tg = []

        for i in range(self.max_concurrent_requests):
            tg.append(asyncio.create_task(crawl_worker()))

        # print("waiting to join")
        await q.join()
        # print("joined")

        for i in range(self.max_concurrent_requests):
            # print("putting in a none")
            await q.put(None)

        # print("waiting to gather")
        await asyncio.gather(*tg)
        # print("gathered")

        if len(results.items()) != len(self.in_degree.items()):
            # print("returning value error")
            raise ValueError("Dependency cycle detected")
        
        # print(f"returning results {results}")

        return results
