import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_DATA = Path(PROJECT_ROOT, 'data')
SCHEMAS = Path(PROJECT_ROOT, 'schemas')
DIST = Path(PROJECT_ROOT, 'docs')
LOCALISATION_DATA = Path(PROJECT_ROOT, 'localisation')


def load_json_file(file: Path) -> list | dict:
    try:
        return json.loads(file.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f'{file}: {e}') from e


def write_data_json(dst: Path, data: list | dict) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=False)
