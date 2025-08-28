import json
import logging
from pathlib import Path
from typing import List, Dict, Union, Any

import jsonschema

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_DATA = Path(PROJECT_ROOT, 'data')
DIST = Path(PROJECT_ROOT, 'docs')
LOCAL_DATA = Path(PROJECT_ROOT, 'local', 'data')
LOCALISATION_DATA = Path(PROJECT_ROOT, 'localisation')

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

class DataPayload:
    """
    The template for handling data. Can be subclassed for other data types (xlsx) in future. Currently intended to
    load data from a single data file (e.g. data/fighters.json).
    """

    def __init__(self, src: Path, schema: Path, src_format: str = None):
        self.src = src
        self.src_format = src_format if src_format else src.suffix  # xlsx, json, csv etc
        self.schema = schema
        self.data = self.load_data()
        self.validate_data()

    def load_data(self):
        raise NotImplementedError('Subclass must implement load_data method')

    def write_to_disk(self, dst: Path = None):
        raise NotImplementedError('Subclass must implement write_to_disk method')

    def validate_data(self):
        raise NotImplementedError('Subclass must implement validate_data method')


class JSONDataPayload(DataPayload):
    def load_data(self):
        data = load_json_file(self.src)
        return data

    def write_to_disk(self, dst: Path = None):
        self.validate_data()
        if not dst:
            dst = self.src
        print(f'writing to {dst}')
        with open(dst, 'w') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            schema_data = json.load(f)
        jsonschema.validate(self.data, schema_data)
