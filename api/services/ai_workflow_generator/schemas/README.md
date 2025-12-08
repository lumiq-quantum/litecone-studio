# Workflow Schema Directory

This directory contains JSON Schema definitions for workflow validation.

## Overview

The schema-driven validation system allows workflows to be validated against versioned JSON schemas. This provides:

1. **Schema Evolution**: Support for multiple schema versions simultaneously
2. **Automatic Version Detection**: Workflows can specify their schema version or have it auto-detected
3. **Clear Error Messages**: Validation errors include specific paths and helpful descriptions
4. **Extensibility**: New schema versions can be added without code changes

## Schema Files

Schema files follow the naming convention: `workflow_schema_v{version}.json`

Example:
- `workflow_schema_v1.json` - Version 1.0.0 of the workflow schema

## Schema Structure

Each schema file must include:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://workflow-orchestrator.com/schemas/workflow/v1",
  "title": "Workflow Definition Schema",
  "version": "1.0.0",
  "type": "object",
  "required": ["name", "start_step", "steps"],
  "properties": {
    // Schema properties...
  }
}
```

### Required Fields

- `$schema`: JSON Schema version (use draft-07)
- `$id`: Unique identifier for the schema
- `title`: Human-readable title
- `version`: Semantic version string (e.g., "1.0.0")
- `type`: Must be "object"
- `required`: Array of required top-level fields
- `properties`: Object defining all workflow properties

## Workflow Schema Properties

### Top-Level Properties

- `name` (string, required): Unique workflow name
- `description` (string, optional): Workflow description
- `start_step` (string, required): ID of the first step to execute
- `steps` (object, required): Map of step IDs to step definitions
- `schema_version` (string, optional): Explicit schema version hint

### Step Properties

Each step in the `steps` object must have:

- `id` (string, required): Unique step identifier
- `type` (string, required): Step type - one of:
  - `agent`: Execute an agent
  - `parallel`: Execute multiple steps in parallel
  - `conditional`: Conditional branching
  - `loop`: Iterate over a collection

#### Agent Steps

Required fields:
- `agent_name` (string): Name of the agent to invoke
- `input_mapping` (object): Map of input field names to value expressions

Optional fields:
- `next_step` (string|null): ID of the next step

#### Parallel Steps

Required fields:
- `parallel_steps` (array): List of step IDs to execute in parallel (minimum 2)

Optional fields:
- `max_parallelism` (integer): Maximum concurrent executions
- `next_step` (string|null): ID of the next step

#### Conditional Steps

Required fields:
- `condition` (object): Condition to evaluate
  - `expression` (string): Condition expression
  - `operator` (string, optional): Simple operator

At least one of:
- `if_true_step` (string|null): Step to execute if condition is true
- `if_false_step` (string|null): Step to execute if condition is false

Optional fields:
- `next_step` (string|null): ID of the next step

#### Loop Steps

Required fields:
- `loop_config` (object): Loop configuration
  - `collection` (string): Reference to collection
  - `loop_body` (array): Step IDs to execute for each item (minimum 1)
  - `execution_mode` (string, optional): "sequential" or "parallel"
  - `max_parallelism` (integer, optional): Max concurrent iterations
  - `max_iterations` (integer, optional): Max iterations to process
  - `on_error` (string, optional): Error handling - "continue", "stop", or "collect"

Optional fields:
- `next_step` (string|null): ID of the next step

## Usage

### Loading Schemas

```python
from api.services.ai_workflow_generator.schema_loader import SchemaLoader

# Load all schemas from default directory
loader = SchemaLoader()

# Or specify custom directory
loader = SchemaLoader(schema_dir="/path/to/schemas")
```

### Validating Workflows

```python
# Validate with auto-detected version
errors = loader.validate(workflow_json)

# Validate with specific version
errors = loader.validate(workflow_json, version_string="1.0.0")

# Check if valid
if not errors:
    print("Workflow is valid!")
else:
    for error in errors:
        print(f"Error: {error}")
```

### Version Detection

```python
# Detect appropriate schema version
schema = loader.detect_version(workflow_json)
print(f"Detected version: {schema.version_string}")

# Get available versions
versions = loader.get_available_versions()
print(f"Available versions: {versions}")

# Get latest version
latest = loader.get_latest_version()
print(f"Latest version: {latest}")
```

### Integration with Validation Service

```python
from api.services.ai_workflow_generator.workflow_validation import (
    WorkflowValidationService
)
from api.services.ai_workflow_generator.schema_loader import SchemaLoader

# Create validation service with schema loader
schema_loader = SchemaLoader()
validation_service = WorkflowValidationService(
    db=db_session,
    schema_loader=schema_loader
)

# Validate workflow
result = await validation_service.validate_workflow(workflow_json)

if result.is_valid:
    print("Workflow is valid!")
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

## Adding New Schema Versions

To add a new schema version:

1. Create a new schema file: `workflow_schema_v{version}.json`
2. Set the `version` field to the new version number
3. Define the schema structure following JSON Schema draft-07
4. Place the file in this directory
5. The schema loader will automatically detect and load it

Example for version 2.0.0:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://workflow-orchestrator.com/schemas/workflow/v2",
  "title": "Workflow Definition Schema v2",
  "version": "2.0.0",
  "type": "object",
  "required": ["name", "start_step", "steps"],
  "properties": {
    // Updated schema properties...
  }
}
```

## Schema Evolution Best Practices

1. **Semantic Versioning**: Use semantic versioning (MAJOR.MINOR.PATCH)
   - MAJOR: Breaking changes
   - MINOR: New features, backward compatible
   - PATCH: Bug fixes, backward compatible

2. **Backward Compatibility**: When possible, maintain backward compatibility
   - Add new optional fields instead of changing existing ones
   - Use default values for new fields
   - Deprecate fields gradually rather than removing them

3. **Version Detection**: Workflows can specify their schema version:
   ```json
   {
     "schema_version": "1.0.0",
     "name": "my-workflow",
     ...
   }
   ```

4. **Migration**: Provide migration guides when introducing breaking changes

## Testing

Tests for schema validation are located in:
- `api/tests/ai_workflow_generator/test_schema_loader.py`
- `api/tests/ai_workflow_generator/test_schema_validation_integration.py`

Run tests:
```bash
pytest api/tests/ai_workflow_generator/test_schema_loader.py -v
pytest api/tests/ai_workflow_generator/test_schema_validation_integration.py -v
```

## Error Messages

The schema loader provides clear, actionable error messages:

- **Missing Required Field**: `Missing required field 'name' at root`
- **Invalid Type**: `Invalid type at steps.step1.type: expected string, got int`
- **Invalid Enum Value**: `Invalid value at steps.step1.type: must be one of [agent, parallel, conditional, loop]`
- **Pattern Mismatch**: `Value at steps.step1.id does not match required pattern: ^[a-zA-Z0-9_-]+$`
- **Array Too Short**: `Array at steps.parallel1.parallel_steps has too few items (minimum: 2)`

## Dependencies

- `jsonschema>=4.20.0`: JSON Schema validation
- `packaging>=23.2`: Version comparison

## Future Enhancements

Potential future improvements:

1. **Schema Registry**: Central registry for schema versions
2. **Schema Migration Tools**: Automated workflow migration between versions
3. **Schema Documentation Generator**: Auto-generate documentation from schemas
4. **Custom Validators**: Support for custom validation rules
5. **Schema Composition**: Support for schema inheritance and composition
