"""
File I/O operations for Warcry data processing.

Pure file loading, writing, validation and filename sanitization.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Union, Any

import jsonschema

logger = logging.getLogger(__name__)


class FileLoadingError(Exception):
    """Raised when file loading fails."""
    pass


def sanitise_filename(filename: str) -> str:
    for illegal_char in r'\\/:*?\"<>|':
        filename = str(filename).replace(illegal_char, '')

    return filename.lower().replace(' ', '_')


def load_json_file(file: Path) -> Any:
    """Load and parse JSON file with proper error handling and encoding fallback.

    Attempts UTF-8 first, falls back to latin-1 for legacy files.

    Args:
        file: Path to JSON file to load

    Returns:
        Parsed JSON data

    Raises:
        FileLoadingError: If file cannot be loaded or parsed
    """
    try:
        return json.loads(file.read_text(encoding='utf-8'))
    except UnicodeDecodeError:
        # Fallback to latin-1 for legacy files
        logger.warning(f"UTF-8 decode failed for {file}, trying latin-1")
        try:
            return json.loads(file.read_text(encoding='latin-1'))
        except UnicodeDecodeError as e:
            raise FileLoadingError(f"Could not decode file {file} with UTF-8 or latin-1: {e}") from e
    except json.JSONDecodeError as e:
        raise FileLoadingError(f"Invalid JSON in {file}: {e}") from e
    except Exception as e:
        raise FileLoadingError(f"Unexpected error reading {file}: {e}") from e


def write_data_json(dst: Path, data: Union[List, Dict], encoding: str = 'utf-8'):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w', encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=False)


def validate_against_schema(data: Any, schema_path: Path) -> None:
    """Validate data against JSON schema.

    Args:
        data: Data to validate (dict, list, etc.)
        schema_path: Path to JSON schema file

    Raises:
        jsonschema.ValidationError: If validation fails
        FileLoadingError: If schema file cannot be loaded
    """
    schema = load_json_file(schema_path)
    jsonschema.validate(data, schema)
