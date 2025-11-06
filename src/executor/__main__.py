"""Entry point for the executor package when run as a module."""

from src.executor.centralized_executor import main
import asyncio

if __name__ == '__main__':
    asyncio.run(main())
