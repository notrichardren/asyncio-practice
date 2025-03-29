import asyncio
import unittest
from unittest.mock import patch, MagicMock
import random
from web_crawler import WebCrawler, fetch_page

class TestWebCrawlerSimplified(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        random.seed(42)  # For reproducible tests
        
    def tearDown(self):
        self.loop.close()
        
    def test_init(self):
        # Test initialization with valid parameters
        crawler = WebCrawler(max_concurrent_requests=5)
        self.assertEqual(crawler.max_concurrent_requests, 5)
        
        # Test initialization with invalid parameters
        with self.assertRaises(ValueError):
            WebCrawler(max_concurrent_requests=0)
        with self.assertRaises(ValueError):
            WebCrawler(max_concurrent_requests=-1)
            
    def test_add_url(self):
        # Test adding URLs with and without dependencies
        crawler = WebCrawler()
        
        async def test():
            await crawler.add_url("https://example.com/page1")
            await crawler.add_url("https://example.com/page2", ["https://example.com/page1"])
            
        self.loop.run_until_complete(test())
        
    def test_crawl_no_dependencies(self):
        # Test crawling URLs with no dependencies
        crawler = WebCrawler(max_concurrent_requests=2)
        
        async def mock_fetch_page(url):
            await asyncio.sleep(0.1)  # Simulate network latency
            return f"Content of {url}"
            
        async def test():
            await crawler.add_url("https://example.com/page1")
            await crawler.add_url("https://example.com/page2")
            
            with patch('web_crawler.fetch_page', side_effect=mock_fetch_page):
                results = await crawler.crawl()
                
            self.assertEqual(len(results), 2)
            self.assertIn("https://example.com/page1", results)
            self.assertIn("https://example.com/page2", results)
            self.assertEqual(results["https://example.com/page1"], "Content of https://example.com/page1")
            self.assertEqual(results["https://example.com/page2"], "Content of https://example.com/page2")
            
        self.loop.run_until_complete(test())
        
    def test_crawl_with_dependencies(self):
        # Test crawling URLs with dependencies
        crawler = WebCrawler(max_concurrent_requests=1)
        
        crawled_order = []
        
        async def mock_fetch_page(url):
            crawled_order.append(url)
            await asyncio.sleep(0.1)  # Simulate network latency
            return f"Content of {url}"
            
        async def test():
            await crawler.add_url("https://example.com/page1")
            await crawler.add_url("https://example.com/page2", ["https://example.com/page1"])
            await crawler.add_url("https://example.com/page3", ["https://example.com/page2"])
            
            with patch('web_crawler.fetch_page', side_effect=mock_fetch_page):
                results = await crawler.crawl()
                
            # Check crawl order respects dependencies
            self.assertEqual(crawled_order[0], "https://example.com/page1")
            self.assertEqual(crawled_order[1], "https://example.com/page2")
            self.assertEqual(crawled_order[2], "https://example.com/page3")
            
        self.loop.run_until_complete(test())
        
    def test_crawl_respects_concurrency_limit(self):
        # Test that crawling respects the concurrency limit
        crawler = WebCrawler(max_concurrent_requests=2)
        
        active_requests = 0
        max_active_requests = 0
        
        async def mock_fetch_page(url):
            nonlocal active_requests, max_active_requests
            active_requests += 1
            max_active_requests = max(max_active_requests, active_requests)
            await asyncio.sleep(0.2)  # Long enough to ensure overlap
            active_requests -= 1
            return f"Content of {url}"
            
        async def test():
            for i in range(5):
                await crawler.add_url(f"https://example.com/page{i}")
                
            with patch('web_crawler.fetch_page', side_effect=mock_fetch_page):
                await crawler.crawl()
                
            # Check that we never exceeded the concurrency limit
            self.assertLessEqual(max_active_requests, 2)
            
        self.loop.run_until_complete(test())
        
    def test_crawl_circular_dependencies(self):
        # Test handling of circular dependencies
        crawler = WebCrawler()
        
        async def test():
            await crawler.add_url("https://example.com/page1")
            await crawler.add_url("https://example.com/page2", ["https://example.com/page1"])
            await crawler.add_url("https://example.com/page3", ["https://example.com/page2"])
            await crawler.add_url("https://example.com/page1", ["https://example.com/page3"])  # Creates a cycle
            
            with self.assertRaises(ValueError):
                await crawler.crawl()
                
        self.loop.run_until_complete(test())
        
    def test_crawl_error_handling(self):
        # Test handling of errors during crawling
        crawler = WebCrawler()
        
        async def failing_fetch_page(url):
            if url == "https://example.com/error":
                raise Exception("Simulated fetch error")
            await asyncio.sleep(0.1)
            return f"Content of {url}"
            
        async def test():
            await crawler.add_url("https://example.com/page1")
            await crawler.add_url("https://example.com/error")
            await crawler.add_url("https://example.com/page2")
            
            with patch('web_crawler.fetch_page', side_effect=failing_fetch_page):
                results = await crawler.crawl()
                
            # Should have results for the successful fetches
            self.assertIn("https://example.com/page1", results)
            self.assertIn("https://example.com/page2", results)
            
            # Should have an error indicator for the failed fetch
            self.assertIn("https://example.com/error", results)
            self.assertEqual(results["https://example.com/error"], "ERROR")
            
        self.loop.run_until_complete(test())
        
    def test_crawl_dependency_error_handling(self):
        # Test handling of errors in dependencies
        crawler = WebCrawler()
        
        async def failing_fetch_page(url):
            if url == "https://example.com/error":
                raise Exception("Simulated fetch error")
            await asyncio.sleep(0.1)
            return f"Content of {url}"
            
        async def test():
            await crawler.add_url("https://example.com/error")
            await crawler.add_url("https://example.com/dependent", ["https://example.com/error"])
            
            with patch('web_crawler.fetch_page', side_effect=failing_fetch_page):
                results = await crawler.crawl()
                
            # Should have an error indicator for the failed fetch
            self.assertIn("https://example.com/error", results)
            self.assertEqual(results["https://example.com/error"], "ERROR")
            
            # Dependent URL should still be processed
            self.assertIn("https://example.com/dependent", results)
            
        self.loop.run_until_complete(test())
        
    def test_crawl_complex_dependency_graph(self):
        # Test crawling with a complex dependency graph
        crawler = WebCrawler()
        
        crawled_order = []
        
        async def mock_fetch_page(url):
            crawled_order.append(url)
            await asyncio.sleep(0.05)
            return f"Content of {url}"
            
        async def test():
            # Create a diamond dependency pattern:
            # A -> B -> D
            # A -> C -> D
            await crawler.add_url("A")
            await crawler.add_url("B", ["A"])
            await crawler.add_url("C", ["A"])
            await crawler.add_url("D", ["B", "C"])
            
            with patch('web_crawler.fetch_page', side_effect=mock_fetch_page):
                await crawler.crawl()
                
            # A must be first
            self.assertEqual(crawled_order[0], "A")
            
            # B and C can be in either order
            self.assertIn("B", crawled_order[1:3])
            self.assertIn("C", crawled_order[1:3])
            
            # D must be last
            self.assertEqual(crawled_order[3], "D")
            
        self.loop.run_until_complete(test())
        
    def test_crawl_empty(self):
        # Test crawling with no URLs
        crawler = WebCrawler()
        
        async def test():
            results = await crawler.crawl()
            self.assertEqual(len(results), 0)
            
        self.loop.run_until_complete(test())
        
    def test_dependency_on_self(self):
        # Test handling a URL that depends on itself
        crawler = WebCrawler()
        
        async def test():
            await crawler.add_url("https://example.com/page1", ["https://example.com/page1"])
            
            with self.assertRaises(ValueError):
                await crawler.crawl()
                
        self.loop.run_until_complete(test())
        
    def test_crawl_small_number_of_urls(self):
        # Test with a small number of URLs with simple dependencies
        crawler = WebCrawler(max_concurrent_requests=3)
        
        async def mock_fetch_page(url):
            await asyncio.sleep(0.05)
            return f"Content of {url}"
            
        async def test():
            # Add 10 URLs with some dependencies
            for i in range(10):
                if i < 3:
                    await crawler.add_url(f"https://example.com/page{i}")
                else:
                    # Each page depends on one previous page
                    dep = f"https://example.com/page{i-3}"
                    await crawler.add_url(f"https://example.com/page{i}", [dep])
                    
            with patch('web_crawler.fetch_page', side_effect=mock_fetch_page):
                results = await crawler.crawl()
                
            # Should have results for all URLs
            self.assertEqual(len(results), 10)
            
        self.loop.run_until_complete(test())
        
    def test_fetch_page_real(self):
        # Test the actual fetch_page function (not mocked)
        async def test():
            content = await fetch_page("https://example.com/test")
            self.assertIn("Content of", content)
            self.assertIn("https://example.com/test", content)
            
        self.loop.run_until_complete(test())

if __name__ == "__main__":
    unittest.main()