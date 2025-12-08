# Documentation

This directory contains all project documentation organized by category.

## Directory Structure

### `/api` - API Documentation
- API specifications, endpoints, and usage guides
- Agent interface specifications (A2A protocol)
- Swagger/OpenAPI documentation
- Database setup and schema documentation

### `/ai-workflow-generator` - AI Workflow Generator Documentation
- Natural language workflow generation
- LLM integration (Gemini)
- Chat sessions and interactive refinement
- Agent suggestions and templates
- Document processing and validation

### `/deployment` - Deployment Guides
- Deployment procedures and checklists
- Migration guides and troubleshooting
- Environment configuration
- Service-specific deployment guides (API, UI)
- Docker compose configuration and machine sizing

### `/testing` - Testing Documentation
- Testing architecture and strategies
- Manual testing guides
- Test result reports
- Circuit breaker and feature-specific testing guides

### `/guides` - User Guides
- Quick start guide
- Development guide
- Workflow configuration and format
- Feature-specific usage guides (circuit breaker, logging, etc.)

### `/architecture` - Architecture Documentation
- System architecture overviews
- Component-specific architecture (bridge, agent registry)
- Integration patterns and checklists
- Project structure and cleanup documentation

### `/features` - Feature Documentation
- Core execution patterns (parallel, conditional, loops, fork-join)
- Circuit breaker implementation
- Feature completion summaries and implementation notes

### `/ui` - UI Documentation
- Frontend implementation details
- UI component documentation
- Visualization guides
- Performance and UX improvements

## Quick Links

### Getting Started
- [Quick Reference](QUICK_REFERENCE.md) - Fast access to common commands
- [Quick Start Guide](guides/QUICKSTART.md)
- [Development Guide](guides/DEVELOPMENT.md)
- [Workflow Format](guides/WORKFLOW_FORMAT.md)

### API
- [API Documentation](api/API_DOCUMENTATION.md)
- [A2A Agent Interface](api/A2A_AGENT_INTERFACE.md)
- [Swagger Guide](api/SWAGGER_GUIDE.md)

### AI Workflow Generator
- [AI Workflow Generator Overview](ai-workflow-generator/README.md)
- [API Documentation](ai-workflow-generator/API_DOCUMENTATION.md)
- [API Quick Reference](ai-workflow-generator/API_QUICK_REFERENCE.md)
- [Configuration Guide](ai-workflow-generator/CONFIG_README.md)
- [Troubleshooting](ai-workflow-generator/TROUBLESHOOTING.md)

### Deployment
- [Deployment Guide](deployment/DEPLOYMENT_GUIDE.md)
- [Deployment Now (Quick Deploy)](deployment/DEPLOYMENT_NOW.md)
- [Migration Guide](deployment/MIGRATION_GUIDE.md)
- [Docker Compose Review](deployment/DOCKER_COMPOSE_REVIEW.md)
- [Machine Sizing Reference](deployment/MACHINE_SIZING_QUICK_REFERENCE.md)
- [Pre-Push Checklist](deployment/PRE_PUSH_CHECKLIST.md)
- [UI Build Fix Summary](deployment/UI_BUILD_FIX_SUMMARY.md)

### Architecture
- [Project Structure](architecture/PROJECT_STRUCTURE.md)
- [Cleanup Summary](architecture/CLEANUP_SUMMARY.md)

### Features
- [Parallel Execution](features/parallel_execution.md)
- [Conditional Logic](features/conditional_logic.md)
- [Loop Execution](features/loop_execution.md)
- [Fork-Join Pattern](features/fork_join_pattern.md)
- [Circuit Breaker](features/circuit_breaker.md)

### Testing
- [Testing Architecture](testing/TESTING_ARCHITECTURE.md)
- [Manual Testing Guide](testing/MANUAL_TESTING_GUIDE.md)

## Contributing

When adding new documentation:
1. Place it in the appropriate category folder
2. Update this README with a link
3. Use clear, descriptive filenames
4. Follow the existing documentation style
