"""
Module entry point for executor package.

This allows running the execution consumer as:
    python -m src.executor
"""

import sys
import asyncio

# Check if we should run the consumer or the standalone executor
if len(sys.argv) > 1 and sys.argv[1] == "consumer":
    # Run the execution consumer service
    from src.executor.execution_consumer import main
    asyncio.run(main())
else:
    # Run the standalone centralized executor
    from src.executor.centralized_executor import main
    asyncio.run(main())
