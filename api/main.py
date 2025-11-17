"""Main FastAPI application for Workflow Management API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from api.config import settings
from api.routes import agents, workflows, runs, system
from api.middleware import register_exception_handlers, register_logging_middleware

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enhanced API description with markdown formatting
api_description = """
# Workflow Management API

A comprehensive REST API for managing workflow orchestration in the Centralized Executor system.

## Features

* **Agent Management**: Register and manage external agents that execute workflow steps
* **Workflow Definitions**: Create, version, and manage workflow templates
* **Workflow Execution**: Trigger and monitor workflow runs asynchronously
* **Run Management**: Track execution status, retry failed runs, and cancel active workflows
* **Health & Monitoring**: Built-in health checks and Prometheus metrics

## Architecture

The API follows a layered architecture:
- **Routes**: REST endpoints for client interaction
- **Services**: Business logic and orchestration
- **Repositories**: Data access layer
- **Models**: Database entities and schemas

## Getting Started

1. **Register Agents**: Create agent records for your external services
2. **Define Workflows**: Build workflow definitions with sequential steps
3. **Execute Workflows**: Trigger executions with input data
4. **Monitor Progress**: Track run status and view step executions

## Authentication

Currently, authentication is not enforced. This will be added in a future release.

## Support

For issues and questions, please refer to the project documentation.
"""

# Create FastAPI app with enhanced OpenAPI configuration
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Agents",
            "description": "Manage external agents that execute workflow steps. "
                          "Agents are services that implement the A2A protocol and can be "
                          "dynamically registered, updated, and health-checked."
        },
        {
            "name": "Workflows",
            "description": "Create and manage workflow definitions. Workflows are directed "
                          "acyclic graphs (DAGs) of steps that define the execution flow. "
                          "Each workflow can have multiple versions for tracking changes."
        },
        {
            "name": "Runs",
            "description": "Monitor and control workflow executions. Runs represent specific "
                          "execution instances of workflows with their own input data, status, "
                          "and step executions. Supports retry and cancellation operations."
        },
        {
            "name": "System",
            "description": "System health checks and monitoring endpoints. Includes liveness "
                          "probes, readiness checks with dependency validation, and Prometheus "
                          "metrics for observability."
        }
    ],
    contact={
        "name": "Workflow Management API Support",
        "url": "https://github.com/your-org/workflow-management-api",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "http://api.example.com",
            "description": "Production server"
        }
    ],
    responses={
        400: {
            "description": "Bad Request - Invalid input data or validation failed"
        },
        404: {
            "description": "Not Found - Requested resource does not exist"
        },
        422: {
            "description": "Unprocessable Entity - Request validation failed"
        },
        500: {
            "description": "Internal Server Error - Unexpected server error occurred"
        },
        503: {
            "description": "Service Unavailable - Service or dependencies are not available"
        }
    }
)

# Register exception handlers
register_exception_handlers(app)

# Register logging middleware (should be registered before other middleware)
register_logging_middleware(app)

# Configure CORS
cors_origins = settings.get_cors_origins_list() if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.get_cors_methods_list(),
    allow_headers=settings.get_cors_headers_list(),
)

# Register routers
app.include_router(agents.router, prefix=settings.api_prefix)
app.include_router(workflows.router, prefix=settings.api_prefix)
app.include_router(runs.router, prefix=settings.api_prefix)
app.include_router(system.router)  # System routes (health, metrics) at root level

# Root endpoint
@app.get(
    "/",
    tags=["System"],
    summary="API information",
    description="Returns basic information about the API including version and documentation links.",
    response_description="API metadata and documentation links"
)
async def root():
    """
    Get API information and documentation links.
    
    This endpoint provides basic information about the API including:
    - API name and version
    - Links to interactive documentation (Swagger UI and ReDoc)
    - OpenAPI specification URL
    - Available API endpoints
    
    Returns:
        dict: API metadata and documentation links
    
    Example:
        GET /
        
        Response:
        {
            "name": "Workflow Management API",
            "version": "1.0.0",
            "description": "REST API for managing workflow orchestration",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_spec": "/openapi.json"
            },
            "endpoints": {
                "agents": "/api/v1/agents",
                "workflows": "/api/v1/workflows",
                "runs": "/api/v1/runs",
                "health": "/health"
            }
        }
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        },
        "endpoints": {
            "agents": f"{settings.api_prefix}/agents",
            "workflows": f"{settings.api_prefix}/workflows",
            "runs": f"{settings.api_prefix}/runs",
            "health": "/health",
            "health_ready": "/health/ready",
            "metrics": "/metrics"
        },
        "status": "operational"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"API documentation available at /docs")
    # TODO: Initialize database connection
    # TODO: Initialize Kafka producer

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.api_title}")
    # TODO: Close database connection
    # TODO: Close Kafka producer

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
