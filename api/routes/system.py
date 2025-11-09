"""
System health and monitoring API routes.

This module provides REST endpoints for system health checks, readiness probes,
and metrics collection for monitoring and observability.

Requirements:
- 10.1: Basic health check via GET /health
- 10.2: Readiness check with DB connectivity via GET /health/ready
- 10.3: Prometheus metrics via GET /metrics
- 10.4: Database connectivity validation
- 10.5: Metrics for request count, latency, and error rate
"""

import time
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.config import settings
from api.schemas.common import HealthResponse, HealthStatus, ReadinessResponse


# Create router with tags
router = APIRouter(tags=["System"])

# Track application start time for uptime calculation
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns the basic health status of the API service. This is a lightweight "
                "check that doesn't verify external dependencies.",
    responses={
        200: {
            "description": "Service is healthy",
            "model": HealthResponse
        }
    }
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    This endpoint provides a simple liveness probe that returns the service status
    without checking external dependencies. It's useful for container orchestration
    systems to determine if the service is running.
    
    Returns:
        HealthResponse: Basic health status with version and uptime
    """
    uptime = time.time() - _start_time
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.api_version,
        uptime_seconds=uptime,
        services=None
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check with dependency validation",
    description="Returns the readiness status of the API service including checks for "
                "database connectivity and other critical dependencies. Use this for "
                "readiness probes in container orchestration.",
    responses={
        200: {
            "description": "Service is ready to accept requests",
            "model": ReadinessResponse
        },
        503: {
            "description": "Service is not ready (dependencies unavailable)",
            "model": ReadinessResponse
        }
    }
)
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> ReadinessResponse:
    """
    Readiness check endpoint with dependency validation.
    
    This endpoint performs health checks on critical dependencies:
    - Database connectivity
    - (Future: Kafka connectivity)
    
    If any critical dependency is unavailable, the endpoint returns 503 Service Unavailable.
    This is useful for container orchestration systems to determine if the service is
    ready to accept traffic.
    
    Args:
        response: FastAPI response object for setting status code
        db: Database session dependency
    
    Returns:
        ReadinessResponse: Readiness status with individual dependency checks
    """
    checks: Dict[str, HealthStatus] = {}
    all_ready = True
    
    # Check database connectivity
    db_start = time.time()
    try:
        # Execute a simple query to verify database connection
        await db.execute(text("SELECT 1"))
        db_time = (time.time() - db_start) * 1000  # Convert to milliseconds
        
        checks["database"] = HealthStatus(
            status="healthy",
            message="Database connection active",
            response_time_ms=round(db_time, 2)
        )
    except Exception as e:
        all_ready = False
        checks["database"] = HealthStatus(
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            response_time_ms=None
        )
    
    # TODO: Add Kafka connectivity check when KafkaService is available
    # For now, we'll add a placeholder that assumes Kafka is healthy
    # This should be implemented in Phase 8 when integrating with the executor
    checks["kafka"] = HealthStatus(
        status="unknown",
        message="Kafka health check not yet implemented",
        response_time_ms=None
    )
    
    # Set appropriate status code
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return ReadinessResponse(
        ready=all_ready,
        timestamp=datetime.utcnow(),
        checks=checks
    )


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Prometheus metrics endpoint",
    description="Returns Prometheus-compatible metrics for monitoring. This is a placeholder "
                "implementation that will be enhanced with actual metrics collection.",
    responses={
        200: {
            "description": "Prometheus metrics in text format",
            "content": {
                "text/plain": {
                    "example": "# HELP api_requests_total Total number of API requests\n"
                              "# TYPE api_requests_total counter\n"
                              "api_requests_total 1234\n"
                }
            }
        }
    },
    response_class=Response
)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint (placeholder).
    
    This endpoint returns Prometheus-compatible metrics in text format.
    Currently, this is a placeholder implementation. In Phase 10, this will be
    enhanced with actual metrics collection using prometheus-fastapi-instrumentator
    or similar libraries.
    
    Planned metrics:
    - api_requests_total: Total number of API requests
    - api_request_duration_seconds: Request duration histogram
    - api_requests_in_progress: Number of requests currently being processed
    - workflow_executions_total: Total number of workflow executions
    - workflow_execution_duration_seconds: Workflow execution duration histogram
    - workflow_execution_failures_total: Total number of failed workflow executions
    
    Returns:
        Response: Prometheus metrics in text/plain format
    """
    # Placeholder metrics
    # TODO: Implement actual metrics collection in Phase 10 (Task 38)
    uptime = time.time() - _start_time
    
    metrics_text = f"""# HELP api_info API information
# TYPE api_info gauge
api_info{{version="{settings.api_version}"}} 1

# HELP api_uptime_seconds API uptime in seconds
# TYPE api_uptime_seconds gauge
api_uptime_seconds {uptime:.2f}

# HELP api_requests_total Total number of API requests (placeholder)
# TYPE api_requests_total counter
api_requests_total 0

# HELP api_request_duration_seconds API request duration in seconds (placeholder)
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{{le="0.1"}} 0
api_request_duration_seconds_bucket{{le="0.5"}} 0
api_request_duration_seconds_bucket{{le="1.0"}} 0
api_request_duration_seconds_bucket{{le="5.0"}} 0
api_request_duration_seconds_bucket{{le="+Inf"}} 0
api_request_duration_seconds_sum 0
api_request_duration_seconds_count 0

# HELP workflow_executions_total Total number of workflow executions (placeholder)
# TYPE workflow_executions_total counter
workflow_executions_total 0

# HELP workflow_execution_failures_total Total number of failed workflow executions (placeholder)
# TYPE workflow_execution_failures_total counter
workflow_execution_failures_total 0
"""
    
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )
