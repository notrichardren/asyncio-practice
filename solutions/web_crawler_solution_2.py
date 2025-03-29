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
            raise ValueError("max_concurrent_requests must be positive")
        
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Store URLs and their dependencies
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
    
    def _detect_cycles(self):
        """Check for cycles in the dependency graph using Kahn's algorithm."""
        # Make a copy of the in-degree dict to avoid modifying the original
        temp_in_degree = self.in_degree.copy()
        
        # Find all nodes with no incoming edges
        no_incoming = [url for url, count in temp_in_degree.items() if count == 0]
        
        # Count processed nodes
        processed = 0
        
        # Process nodes with no incoming edges
        while no_incoming:
            current = no_incoming.pop(0)
            processed += 1
            
            # For each neighbor, reduce in-degree and check if it's now ready
            for neighbor in self.out_neighbors[current]:
                temp_in_degree[neighbor] -= 1
                if temp_in_degree[neighbor] == 0:
                    no_incoming.append(neighbor)
        
        # If we couldn't process all nodes, there's a cycle
        return processed != len(self.in_degree)
        
    async def crawl(self) -> Dict[str, str]:
        """
        Crawl all added URLs, respecting dependencies and concurrency limits.
        
        Returns:
            A dictionary mapping URLs to their page content
        """
        if not self.in_degree:  # Empty graph
            return {}
            
        # Check for cycles BEFORE starting the crawl
        if self._detect_cycles():
            raise ValueError("Dependency cycle detected")

        # Set up crawling
        q = asyncio.Queue()
        results = {}
        
        # Add URLs with no dependencies to the queue
        for url, count in self.in_degree.items():
            if count == 0:
                await q.put(url)
                
        # Set up a done event to signal when crawling is complete
        done_event = asyncio.Event()
                
        async def crawl_worker():
            try:
                while not done_event.is_set():
                    try:
                        # Get next URL with a timeout to check for done_event periodically
                        url = await asyncio.wait_for(q.get(), timeout=0.5)
                    except asyncio.TimeoutError:
                        # No items in queue, check if we should exit
                        continue
                        
                    # Process the URL
                    async with self.semaphore:
                        try:
                            result = await fetch_page(url)
                        except Exception:
                            result = "ERROR"
                            
                        async with self.lock:
                            # Store the result
                            results[url] = result
                            
                            # Update dependencies
                            for neighbor in self.out_neighbors[url]:
                                self.in_degree[neighbor] -= 1
                                if self.in_degree[neighbor] == 0:
                                    await q.put(neighbor)
                                    
                    # Mark task as done
                    q.task_done()
            except asyncio.CancelledError:
                # Handle task cancellation
                pass
                
        # Create worker tasks
        workers = []
        for _ in range(self.max_concurrent_requests):
            task = asyncio.create_task(crawl_worker())
            workers.append(task)
            
        try:
            # Wait for all items to be processed
            await q.join()
            
            # Signal workers to exit
            done_event.set()
            
            # Wait for all workers to finish
            await asyncio.gather(*workers)
            
            return results
        except Exception:
            # If any exception occurs, cancel all worker tasks
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            raise