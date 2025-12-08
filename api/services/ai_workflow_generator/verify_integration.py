"""Verification script for AI Workflow Generator integration.

This script verifies that the AI Workflow Generator is properly integrated
with the main API infrastructure.
"""

import sys
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_routes_registered() -> bool:
    """Verify that AI workflow routes are registered."""
    try:
        from api.main import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Check for AI workflow routes
        required_routes = [
            "/api/v1/ai-workflows/generate",
            "/api/v1/ai-workflows/upload",
            "/api/v1/ai-workflows/chat/sessions",
            "/api/v1/ai-workflows/agents/suggest",
        ]
        
        missing_routes = [route for route in required_routes if route not in routes]
        
        if missing_routes:
            logger.error(f"Missing routes: {missing_routes}")
            return False
        
        logger.info("✓ All AI workflow routes are registered")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify routes: {e}")
        return False


def verify_model_imported() -> bool:
    """Verify that ChatSessionModel is properly imported."""
    try:
        from api.models import ChatSessionModel
        
        # Check table name
        if ChatSessionModel.__tablename__ != "ai_chat_sessions":
            logger.error(f"Unexpected table name: {ChatSessionModel.__tablename__}")
            return False
        
        # Check key attributes
        required_attrs = ["id", "user_id", "status", "current_workflow", "messages"]
        missing_attrs = [attr for attr in required_attrs if not hasattr(ChatSessionModel, attr)]
        
        if missing_attrs:
            logger.error(f"Missing attributes: {missing_attrs}")
            return False
        
        logger.info("✓ ChatSessionModel is properly imported and configured")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify model: {e}")
        return False


def verify_middleware_configured() -> bool:
    """Verify that middleware is properly configured."""
    try:
        from api.main import app
        
        # Check that middleware is registered
        middleware_count = len(app.user_middleware)
        
        if middleware_count == 0:
            logger.warning("No middleware registered (this may be expected in some configurations)")
        else:
            logger.info(f"✓ {middleware_count} middleware components registered")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify middleware: {e}")
        return False


def verify_health_checks() -> bool:
    """Verify that health check endpoints exist."""
    try:
        from api.main import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Check for health check routes
        required_health_routes = [
            "/health",
            "/health/ready",
            "/health/ai",
        ]
        
        missing_routes = [route for route in required_health_routes if route not in routes]
        
        if missing_routes:
            logger.error(f"Missing health check routes: {missing_routes}")
            return False
        
        logger.info("✓ All health check endpoints are registered")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify health checks: {e}")
        return False


def verify_configuration() -> bool:
    """Verify that configuration is properly loaded."""
    try:
        from api.services.ai_workflow_generator.config import ai_workflow_config
        
        # Check key configuration values
        if not ai_workflow_config.gemini_model:
            logger.error("Gemini model not configured")
            return False
        
        if not ai_workflow_config.agent_registry_url:
            logger.error("Agent registry URL not configured")
            return False
        
        if not ai_workflow_config.workflow_api_url:
            logger.error("Workflow API URL not configured")
            return False
        
        logger.info("✓ Configuration is properly loaded")
        logger.info(f"  - Gemini Model: {ai_workflow_config.gemini_model}")
        logger.info(f"  - Agent Registry: {ai_workflow_config.agent_registry_url}")
        logger.info(f"  - Workflow API: {ai_workflow_config.workflow_api_url}")
        
        # Check if API key is configured (but don't log it)
        if not ai_workflow_config.gemini_api_key:
            logger.warning("⚠ Gemini API key is not configured (set GEMINI_API_KEY)")
        else:
            logger.info("✓ Gemini API key is configured")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify configuration: {e}")
        return False


def verify_migration_exists() -> bool:
    """Verify that the chat sessions migration exists."""
    try:
        import os
        migration_path = "api/migrations/versions/002_add_ai_chat_sessions.py"
        
        if not os.path.exists(migration_path):
            logger.error(f"Migration file not found: {migration_path}")
            return False
        
        logger.info("✓ Chat sessions migration file exists")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify migration: {e}")
        return False


def main() -> int:
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("AI Workflow Generator Integration Verification")
    logger.info("=" * 60)
    
    checks = [
        ("Routes Registration", verify_routes_registered),
        ("Model Import", verify_model_imported),
        ("Middleware Configuration", verify_middleware_configured),
        ("Health Check Endpoints", verify_health_checks),
        ("Configuration Loading", verify_configuration),
        ("Database Migration", verify_migration_exists),
    ]
    
    results: Dict[str, bool] = {}
    
    for check_name, check_func in checks:
        logger.info(f"\nChecking: {check_name}")
        logger.info("-" * 60)
        results[check_name] = check_func()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {check_name}")
    
    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("\n✓ All integration checks passed!")
        logger.info("The AI Workflow Generator is properly integrated.")
        return 0
    else:
        logger.error(f"\n✗ {total - passed} check(s) failed")
        logger.error("Please review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
