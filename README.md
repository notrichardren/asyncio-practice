# Leetcode-Style Practice Problems for Asyncio

A collection of 30-60 minute LeetCode-style exercises for practicing asyncio basics, alongside comprehensive test cases. These exercises were created because there were very few resources available to *practice* asyncio and get a feel for its edge cases and real-world applications.

## Exercises

### 1. Web Crawler with Dependency Resolution
**Difficulty**: Medium
- Implement an asynchronous web crawler that respects page dependencies
- Handle concurrent requests with rate limiting
- Manage dependency resolution and cycle detection
- Practice with async/await patterns and task management

### 2. Rate Limiter
**Difficulty**: Easy-Medium
- Build an asynchronous rate limiter for API requests
- Implement token bucket algorithm
- Handle concurrent operations efficiently
- Practice with async primitives and timing

## Project Structure
```
practice_asyncio/
├── web_crawler/          # Web crawler exercise
├── rate_limiter/         # Rate limiter exercise
└── solutions/            # Reference solutions
```

## Getting Started
Each exercise is self-contained and includes:
- Detailed problem statement
- Requirements and constraints
- Example usage
- Test cases
- Reference solution

To work on an exercise:
1. Navigate to the exercise directory
2. Read the README.md for detailed instructions
3. Implement the required functionality
4. Run the test cases to verify your solution

## Prerequisites
- Python 3.7+
- Basic understanding of asyncio concepts
- Familiarity with async/await syntax
