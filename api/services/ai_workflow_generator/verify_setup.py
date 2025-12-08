"""Verification script to check AI workflow generator setup."""

import sys


def verify_dependencies():
    """Verify that all required dependencies are available."""
    dependencies = {
        "google.generativeai": "Google Generative AI (Gemini)",
        "PyPDF2": "PyPDF2 for PDF processing",
        "docx": "python-docx for DOCX processing",
        "magic": "python-magic for file type detection",
        "hypothesis": "Hypothesis for property-based testing"
    }
    
    missing = []
    available = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            available.append(name)
        except ImportError:
            missing.append(name)
    
    print("AI Workflow Generator Setup Verification")
    print("=" * 50)
    print()
    
    if available:
        print("✓ Available dependencies:")
        for dep in available:
            print(f"  - {dep}")
        print()
    
    if missing:
        print("✗ Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print()
        print("Run: pip install -r api/requirements.txt")
        return False
    else:
        print("✓ All dependencies are installed!")
        return True


def verify_structure():
    """Verify that the directory structure is correct."""
    import os
    
    required_files = [
        "api/services/ai_workflow_generator/__init__.py",
        "api/services/ai_workflow_generator/config.py",
        "api/services/ai_workflow_generator/workflow_generation.py",
        "api/services/ai_workflow_generator/gemini_service.py",
        "api/services/ai_workflow_generator/agent_query.py",
        "api/services/ai_workflow_generator/document_processing.py",
        "api/services/ai_workflow_generator/chat_session.py",
        "api/services/ai_workflow_generator/workflow_validation.py",
        "api/models/ai_workflow.py",
        "api/schemas/ai_workflow.py",
        "api/routes/ai_workflows.py",
        "api/tests/ai_workflow_generator/__init__.py",
        "api/tests/ai_workflow_generator/conftest.py",
    ]
    
    print()
    print("Directory Structure Verification")
    print("=" * 50)
    print()
    
    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing.append(file_path)
    
    if missing:
        print()
        print(f"✗ {len(missing)} files are missing!")
        return False
    else:
        print()
        print("✓ All required files are present!")
        return True


def verify_config():
    """Verify that configuration can be loaded."""
    print()
    print("Configuration Verification")
    print("=" * 50)
    print()
    
    try:
        from api.services.ai_workflow_generator.config import AIWorkflowConfig
        print("✓ Configuration module can be imported")
        
        # Try to load config (will fail if GEMINI_API_KEY is not set, which is expected)
        try:
            config = AIWorkflowConfig()
            print("✓ Configuration loaded successfully")
            print(f"  - Model: {config.gemini_model}")
            print(f"  - Max Tokens: {config.gemini_max_tokens}")
            print(f"  - Session Timeout: {config.session_timeout_minutes} minutes")
            return True
        except Exception as e:
            print(f"⚠ Configuration requires environment variables:")
            print(f"  - GEMINI_API_KEY is required")
            print(f"  - See .env.api.example for all configuration options")
            return True  # This is expected if env vars aren't set
            
    except Exception as e:
        print(f"✗ Failed to import configuration: {e}")
        return False


if __name__ == "__main__":
    print()
    deps_ok = verify_dependencies()
    struct_ok = verify_structure()
    config_ok = verify_config()
    
    print()
    print("=" * 50)
    if deps_ok and struct_ok and config_ok:
        print("✓ Setup verification completed successfully!")
        print()
        print("Next steps:")
        print("1. Set GEMINI_API_KEY in your .env.api file")
        print("2. Run database migrations: alembic upgrade head")
        print("3. Start implementing the service components")
        sys.exit(0)
    else:
        print("✗ Setup verification failed!")
        print("Please fix the issues above before proceeding.")
        sys.exit(1)
