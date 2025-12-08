"""Schema loader for dynamic workflow validation."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from packaging import version
import jsonschema
from jsonschema import Draft7Validator, validators


class SchemaVersion:
    """Represents a schema version."""
    
    def __init__(self, version_string: str, schema_data: Dict[str, Any], file_path: str):
        """
        Initialize schema version.
        
        Args:
            version_string: Version string (e.g., "1.0.0")
            schema_data: The JSON schema data
            file_path: Path to the schema file
        """
        self.version_string = version_string
        self.version = version.parse(version_string)
        self.schema_data = schema_data
        self.file_path = file_path
        self.validator = self._create_validator()
    
    def _create_validator(self) -> Draft7Validator:
        """Create a JSON schema validator with custom error messages."""
        # Extend the validator to provide better error messages
        def extend_with_default(validator_class):
            validate_properties = validator_class.VALIDATORS["properties"]
            
            def set_defaults(validator, properties, instance, schema):
                for property, subschema in properties.items():
                    if "default" in subschema:
                        instance.setdefault(property, subschema["default"])
                
                for error in validate_properties(
                    validator, properties, instance, schema,
                ):
                    yield error
            
            return validators.extend(
                validator_class, {"properties": set_defaults},
            )
        
        DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)
        return DefaultValidatingDraft7Validator(self.schema_data)
    
    def validate(self, workflow_json: Dict[str, Any]) -> List[str]:
        """
        Validate workflow against this schema version.
        
        Args:
            workflow_json: Workflow to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            # Validate against JSON schema
            validation_errors = sorted(
                self.validator.iter_errors(workflow_json),
                key=lambda e: e.path
            )
            
            for error in validation_errors:
                # Build a readable error message
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                
                # Get the specific error message
                if error.validator == "required":
                    missing_property = error.message.split("'")[1]
                    errors.append(
                        f"Missing required field '{missing_property}' at {path}"
                    )
                elif error.validator == "type":
                    expected_type = error.validator_value
                    errors.append(
                        f"Invalid type at {path}: expected {expected_type}, "
                        f"got {type(error.instance).__name__}"
                    )
                elif error.validator == "enum":
                    allowed_values = ", ".join(str(v) for v in error.validator_value)
                    errors.append(
                        f"Invalid value at {path}: must be one of [{allowed_values}]"
                    )
                elif error.validator == "minLength":
                    errors.append(
                        f"Value at {path} is too short (minimum length: {error.validator_value})"
                    )
                elif error.validator == "maxLength":
                    errors.append(
                        f"Value at {path} is too long (maximum length: {error.validator_value})"
                    )
                elif error.validator == "minItems":
                    errors.append(
                        f"Array at {path} has too few items (minimum: {error.validator_value})"
                    )
                elif error.validator == "minProperties":
                    errors.append(
                        f"Object at {path} has too few properties (minimum: {error.validator_value})"
                    )
                elif error.validator == "pattern":
                    errors.append(
                        f"Value at {path} does not match required pattern: {error.validator_value}"
                    )
                else:
                    # Generic error message
                    errors.append(f"Validation error at {path}: {error.message}")
        
        except Exception as e:
            errors.append(f"Schema validation failed: {str(e)}")
        
        return errors
    
    def __str__(self) -> str:
        return f"SchemaVersion({self.version_string})"
    
    def __repr__(self) -> str:
        return f"SchemaVersion(version='{self.version_string}', file='{self.file_path}')"


class SchemaLoader:
    """Loads and manages workflow JSON schemas."""
    
    def __init__(self, schema_dir: Optional[str] = None):
        """
        Initialize the schema loader.
        
        Args:
            schema_dir: Directory containing schema files. If None, uses default location.
        """
        if schema_dir is None:
            # Default to schemas directory relative to this file
            current_dir = Path(__file__).parent
            schema_dir = current_dir / "schemas"
        
        self.schema_dir = Path(schema_dir)
        self.schemas: Dict[str, SchemaVersion] = {}
        self.latest_version: Optional[SchemaVersion] = None
        
        # Load all schemas on initialization
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load all schema files from the schema directory."""
        if not self.schema_dir.exists():
            raise FileNotFoundError(
                f"Schema directory not found: {self.schema_dir}"
            )
        
        # Find all JSON schema files
        schema_files = list(self.schema_dir.glob("workflow_schema_v*.json"))
        
        if not schema_files:
            raise FileNotFoundError(
                f"No schema files found in {self.schema_dir}"
            )
        
        for schema_file in schema_files:
            try:
                with open(schema_file, 'r') as f:
                    schema_data = json.load(f)
                
                # Extract version from schema
                schema_version = schema_data.get("version")
                if not schema_version:
                    # Try to extract from filename
                    # Format: workflow_schema_v1.json -> "1.0.0"
                    filename = schema_file.stem
                    if filename.startswith("workflow_schema_v"):
                        version_part = filename.replace("workflow_schema_v", "")
                        # Convert "1" to "1.0.0"
                        if "." not in version_part:
                            schema_version = f"{version_part}.0.0"
                        else:
                            schema_version = version_part
                    else:
                        continue
                
                # Create SchemaVersion object
                schema_obj = SchemaVersion(
                    schema_version,
                    schema_data,
                    str(schema_file)
                )
                
                self.schemas[schema_version] = schema_obj
                
                # Track latest version
                if (self.latest_version is None or 
                    schema_obj.version > self.latest_version.version):
                    self.latest_version = schema_obj
            
            except Exception as e:
                # Log error but continue loading other schemas
                print(f"Warning: Failed to load schema {schema_file}: {e}")
                continue
        
        if not self.schemas:
            raise ValueError("No valid schemas could be loaded")
    
    def get_schema(self, version_string: Optional[str] = None) -> SchemaVersion:
        """
        Get a specific schema version or the latest version.
        
        Args:
            version_string: Version string (e.g., "1.0.0"). If None, returns latest.
            
        Returns:
            SchemaVersion object
            
        Raises:
            ValueError: If the requested version is not found
        """
        if version_string is None:
            if self.latest_version is None:
                raise ValueError("No schemas available")
            return self.latest_version
        
        if version_string not in self.schemas:
            available = ", ".join(self.schemas.keys())
            raise ValueError(
                f"Schema version '{version_string}' not found. "
                f"Available versions: {available}"
            )
        
        return self.schemas[version_string]
    
    def detect_version(self, workflow_json: Dict[str, Any]) -> SchemaVersion:
        """
        Detect the appropriate schema version for a workflow.
        
        This method attempts to determine which schema version should be used
        to validate the workflow. It checks for version hints in the workflow
        and falls back to trying each schema version.
        
        Args:
            workflow_json: Workflow to analyze
            
        Returns:
            Best matching SchemaVersion
        """
        # Check if workflow specifies a schema version
        if "schema_version" in workflow_json:
            version_string = workflow_json["schema_version"]
            try:
                return self.get_schema(version_string)
            except ValueError:
                # Version not found, fall through to detection
                pass
        
        # Try to validate against each schema, starting with latest
        sorted_schemas = sorted(
            self.schemas.values(),
            key=lambda s: s.version,
            reverse=True
        )
        
        for schema in sorted_schemas:
            errors = schema.validate(workflow_json)
            if not errors:
                # This schema validates successfully
                return schema
        
        # If no schema validates successfully, return latest
        # (validation will fail but at least we have a schema)
        return self.latest_version
    
    def validate(
        self,
        workflow_json: Dict[str, Any],
        version_string: Optional[str] = None
    ) -> List[str]:
        """
        Validate a workflow against a schema.
        
        Args:
            workflow_json: Workflow to validate
            version_string: Specific version to validate against. If None, auto-detects.
            
        Returns:
            List of validation error messages (empty if valid)
        """
        if version_string:
            schema = self.get_schema(version_string)
        else:
            schema = self.detect_version(workflow_json)
        
        return schema.validate(workflow_json)
    
    def get_available_versions(self) -> List[str]:
        """
        Get list of available schema versions.
        
        Returns:
            List of version strings, sorted from oldest to newest
        """
        sorted_schemas = sorted(
            self.schemas.values(),
            key=lambda s: s.version
        )
        return [s.version_string for s in sorted_schemas]
    
    def get_latest_version(self) -> str:
        """
        Get the latest schema version string.
        
        Returns:
            Latest version string
        """
        if self.latest_version is None:
            raise ValueError("No schemas available")
        return self.latest_version.version_string
    
    def reload_schemas(self) -> None:
        """Reload all schemas from disk."""
        self.schemas.clear()
        self.latest_version = None
        self._load_schemas()
