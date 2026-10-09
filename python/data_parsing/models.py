import json
from pathlib import Path
from typing import TypeVar

JsonContainer = TypeVar('JsonContainer', list, dict)

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_DATA = Path(PROJECT_ROOT, 'data')
SCHEMAS = Path(PROJECT_ROOT, 'schemas')
DIST = Path(PROJECT_ROOT, 'docs')
LOCALISATION_DATA = Path(PROJECT_ROOT, 'localisation')


def load_json_file(file: Path, expected: type[JsonContainer]) -> JsonContainer:
    try:
        content = json.loads(file.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f'{file}: {e}') from e
    if not isinstance(content, expected):
        raise ValueError(f'{file}: expected a JSON {expected.__name__}, found {type(content).__name__}')
    return content


def write_data_json(dst: Path, data: list | dict) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=False)
