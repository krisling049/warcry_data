"""
Validation architecture for Warcry data processing.

Provides structured validation results and composable validators.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

import jsonschema

from .config import SchemaFiles

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a single validation error."""
    message: str
    path: str = ""
    value: Any = None
    schema_path: str = ""
    
    def __str__(self) -> str:
        if self.path:
            return f"Error at {self.path}: {self.message}"
        return self.message


@dataclass
class ValidationWarning:
    """Represents a validation warning."""
    message: str
    path: str = ""
    value: Any = None
    
    def __str__(self) -> str:
        if self.path:
            return f"Warning at {self.path}: {self.message}"
        return self.message


@dataclass
class ValidationResult:
    """Comprehensive validation result with errors, warnings and metadata."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    schema_path: Optional[Path] = None
    data_path: Optional[Path] = None
    items_validated: int = 0
    
    def add_error(self, message: str, path: str = "", value: Any = None) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(message, path, value, str(self.schema_path or "")))
        self.is_valid = False
    
    def add_warning(self, message: str, path: str = "", value: Any = None) -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationWarning(message, path, value))
    
    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.items_validated += other.items_validated
        if not other.is_valid:
            self.is_valid = False
    
    def summary(self) -> str:
        """Get a summary of the validation result."""
        status = "PASSED" if self.is_valid else "FAILED"
        return (f"Validation {status}: {self.items_validated} items, "
                f"{len(self.errors)} errors, {len(self.warnings)} warnings")
    
    def detailed_report(self) -> str:
        """Get a detailed validation report."""
        lines = [self.summary()]
        
        if self.schema_path:
            lines.append(f"Schema: {self.schema_path}")
        if self.data_path:
            lines.append(f"Data: {self.data_path}")
        
        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        return "\n".join(lines)


class SchemaValidator:
    """Validates data against JSON schemas."""

    def __init__(self, schema_path: Path):
        """Initialize with schema file path."""
        self.schema_path = schema_path
        try:
            self.schema = json.loads(schema_path.read_text(encoding='utf-8'))
            # Create a custom RefResolver to handle local schema references
            self.resolver = self._create_local_resolver()
        except Exception as e:
            raise ValueError(f"Failed to load schema from {schema_path}: {e}")

    def _create_local_resolver(self) -> jsonschema.RefResolver:
        """Create a RefResolver that resolves remote schema refs to local files."""
        from .config import SchemaFiles

        # Build a store mapping remote URLs to local schema content
        schema_store = {}

        # Map the remote ability schema URL to local file
        ability_schema_path = SchemaFiles.ABILITY
        if ability_schema_path.exists():
            ability_schema = json.loads(ability_schema_path.read_text(encoding='utf-8'))
            schema_store["https://raw.githubusercontent.com/krisling049/warcry_data/main/data/schemas/ability_schema.json"] = ability_schema
            schema_store["https://raw.githubusercontent.com/krisling049/warcry_data/main/schemas/ability_schema.json"] = ability_schema

        # Map fighter schema
        fighter_schema_path = SchemaFiles.FIGHTER
        if fighter_schema_path.exists():
            fighter_schema = json.loads(fighter_schema_path.read_text(encoding='utf-8'))
            schema_store["https://raw.githubusercontent.com/krisling049/warcry_data/main/data/schemas/fighter_schema.json"] = fighter_schema
            schema_store["https://raw.githubusercontent.com/krisling049/warcry_data/main/schemas/fighter_schema.json"] = fighter_schema

        # Create resolver with the store
        return jsonschema.RefResolver.from_schema(self.schema, store=schema_store)
    
    def validate(self, data: Any, data_path: Optional[Path] = None) -> ValidationResult:
        """Validate data against the schema."""
        result = ValidationResult(
            is_valid=True,
            schema_path=self.schema_path,
            data_path=data_path
        )

        try:
            # Validate against schema using custom resolver to avoid remote fetching
            validator = jsonschema.Draft7Validator(self.schema, resolver=self.resolver)

            # Validate the data
            errors = list(validator.iter_errors(data))
            if errors:
                for error in errors:
                    result.add_error(
                        message=error.message,
                        path=".".join(str(p) for p in error.absolute_path),
                        value=error.instance
                    )

            # Count items validated
            if isinstance(data, list):
                result.items_validated = len(data)
            elif isinstance(data, dict):
                result.items_validated = 1
            else:
                result.items_validated = 1

        except jsonschema.SchemaError as e:
            result.add_error(f"Schema error: {e.message}")
        except Exception as e:
            result.add_error(f"Unexpected validation error: {e}")

        return result


class BusinessRuleValidator:
    """Validates data against business rules."""

    def __init__(self):
        from .validation_config import ValidationRules
        self.rules = ValidationRules()

    def validate_fighter(self, fighter_data: Dict[str, Any]) -> ValidationResult:
        """Validate a fighter against business rules."""
        result = ValidationResult(is_valid=True, items_validated=1)

        # Validate points
        points = fighter_data.get('points', 0)
        if not self.rules.is_valid_points_value(points):
            result.add_error(
                f"Invalid points value: {points} (must be {self.rules.min_points}-{self.rules.max_points})",
                path="points",
                value=points
            )

        # Validate movement
        movement = fighter_data.get('movement', 0)
        if not self.rules.is_valid_movement(movement):
            result.add_error(
                f"Invalid movement value: {movement} (must be {self.rules.min_movement}-{self.rules.max_movement})",
                path="movement",
                value=movement
            )

        # Validate toughness
        toughness = fighter_data.get('toughness', 0)
        if not self.rules.is_valid_toughness(toughness):
            result.add_error(
                f"Invalid toughness value: {toughness} (must be {self.rules.min_toughness}-{self.rules.max_toughness})",
                path="toughness",
                value=toughness
            )

        # Validate wounds
        wounds = fighter_data.get('wounds', 0)
        if not self.rules.is_valid_wounds(wounds):
            result.add_error(
                f"Invalid wounds value: {wounds} (must be {self.rules.min_wounds}-{self.rules.max_wounds})",
                path="wounds",
                value=wounds
            )

        # Check for missing required fields (weapons and runemarks can be empty lists)
        required_fields = ['_id', 'name', 'warband', 'grand_alliance']
        for field_name in required_fields:
            if field_name not in fighter_data or not fighter_data[field_name]:
                result.add_error(f"Missing required field: {field_name}", path=field_name)

        # Check weapons and runemarks exist (but can be empty)
        if 'weapons' not in fighter_data:
            result.add_error("Missing required field: weapons", path="weapons")
        if 'runemarks' not in fighter_data:
            result.add_error("Missing required field: runemarks", path="runemarks")

        return result
    
    def validate_ability(self, ability_data: Dict[str, Any]) -> ValidationResult:
        """Validate an ability against business rules."""
        result = ValidationResult(is_valid=True, items_validated=1)

        # Check for missing required fields (runemarks can be empty list)
        required_fields = ['_id', 'name', 'warband', 'cost', 'description']
        for field_name in required_fields:
            if field_name not in ability_data or not ability_data[field_name]:
                result.add_error(f"Missing required field: {field_name}", path=field_name)

        # Check runemarks exists (but can be empty)
        if 'runemarks' not in ability_data:
            result.add_error("Missing required field: runemarks", path="runemarks")
        
        # Validate cost format
        cost = ability_data.get('cost', '')
        valid_costs = ['single', 'double', 'triple', 'quad', 'battletrait', 'reaction', 'passive']
        if cost and cost not in valid_costs:
            result.add_warning(
                f"Unusual cost value: {cost} (expected one of {valid_costs})",
                path="cost",
                value=cost
            )
        
        return result


class CompositeValidator:
    """Combines multiple validators for comprehensive validation."""
    
    def __init__(self):
        """Initialize with all available validators."""
        self.schema_validators = {
            'fighter': SchemaValidator(SchemaFiles.FIGHTER),
            'ability': SchemaValidator(SchemaFiles.ABILITY),
            'faction': SchemaValidator(SchemaFiles.FACTION),
            'fighters_aggregate': SchemaValidator(SchemaFiles.FIGHTERS_AGGREGATE),
            'abilities_aggregate': SchemaValidator(SchemaFiles.ABILITIES_AGGREGATE),
        }
        self.business_validator = BusinessRuleValidator()
    
    def validate_fighters(self, fighters_data: List[Dict[str, Any]], 
                         data_path: Optional[Path] = None) -> ValidationResult:
        """Validate fighters data comprehensively."""
        result = ValidationResult(is_valid=True, data_path=data_path)
        
        # Schema validation
        schema_result = self.schema_validators['fighters_aggregate'].validate(fighters_data, data_path)
        result.merge(schema_result)
        
        # Individual fighter validation
        for i, fighter_data in enumerate(fighters_data):
            fighter_result = self.business_validator.validate_fighter(fighter_data)
            if not fighter_result.is_valid:
                # Add index to error paths
                for error in fighter_result.errors:
                    error.path = f"[{i}].{error.path}" if error.path else f"[{i}]"
                result.merge(fighter_result)
        
        return result
    
    def validate_abilities(self, abilities_data: List[Dict[str, Any]], 
                          data_path: Optional[Path] = None) -> ValidationResult:
        """Validate abilities data comprehensively."""
        result = ValidationResult(is_valid=True, data_path=data_path)
        
        # Schema validation
        schema_result = self.schema_validators['abilities_aggregate'].validate(abilities_data, data_path)
        result.merge(schema_result)
        
        # Individual ability validation
        for i, ability_data in enumerate(abilities_data):
            ability_result = self.business_validator.validate_ability(ability_data)
            if not ability_result.is_valid or ability_result.warnings:
                # Add index to error/warning paths
                for error in ability_result.errors:
                    error.path = f"[{i}].{error.path}" if error.path else f"[{i}]"
                for warning in ability_result.warnings:
                    warning.path = f"[{i}].{warning.path}" if warning.path else f"[{i}]"
                result.merge(ability_result)
        
        return result
    
    def validate_all_data(self, data: Dict[str, List[Dict[str, Any]]]) -> ValidationResult:
        """Validate all data types in a combined result."""
        result = ValidationResult(is_valid=True)

        # Validate fighters
        if 'fighters' in data:
            fighters_result = self.validate_fighters(data['fighters'])
            result.merge(fighters_result)

            # Check for duplicate fighter IDs
            fighter_ids = [f.get('_id') for f in data['fighters'] if '_id' in f]
            seen_ids = set()
            for i, fighter_id in enumerate(fighter_ids):
                if fighter_id in seen_ids:
                    fighter = data['fighters'][i]
                    result.add_error(
                        f"Duplicate fighter ID: {fighter_id}",
                        path=f"fighters[{i}]._id",
                        value=f"{fighter.get('grand_alliance')}/{fighter.get('warband')}/{fighter.get('name')}"
                    )
                seen_ids.add(fighter_id)

        # Validate abilities
        if 'abilities' in data:
            abilities_result = self.validate_abilities(data['abilities'])
            result.merge(abilities_result)

            # Check for duplicate ability IDs
            ability_ids = [a.get('_id') for a in data['abilities'] if '_id' in a]
            seen_ids = set()
            for i, ability_id in enumerate(ability_ids):
                if ability_id in seen_ids:
                    ability = data['abilities'][i]
                    result.add_error(
                        f"Duplicate ability ID: {ability_id}",
                        path=f"abilities[{i}]._id",
                        value=f"{ability.get('warband')}/{ability.get('name')}"
                    )
                seen_ids.add(ability_id)

        logger.info(result.summary())
        
        if result.errors:
            logger.error("Validation failed with errors:")
            for error in result.errors:
                logger.error(f"  {error}")
        
        if result.warnings:
            logger.warning("Validation completed with warnings:")
            for warning in result.warnings:
                logger.warning(f"  {warning}")
        
        return result
