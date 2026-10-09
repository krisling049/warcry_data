import json
from collections import Counter

from jsonschema import Draft201909Validator

from .constants import ABILITIES, FACTIONS, FIGHTERS
from .data_loading import WarbandData
from .models import SCHEMAS

SCHEMA_FILES = {
    FIGHTERS: SCHEMAS / 'fighter_schema.json',
    ABILITIES: SCHEMAS / 'ability_schema.json',
    FACTIONS: SCHEMAS / 'faction_schema.json',
}


def _label(entity: dict) -> str:
    return f"{entity.get('warband', '?')}/{entity.get('name', entity.get('_id', '?'))}"


def validate_data(data: WarbandData) -> list[str]:
    """Return every schema and duplicate-_id error in data; an empty list means valid."""
    errors: list[str] = []
    for data_type, schema_file in SCHEMA_FILES.items():
        validator = Draft201909Validator(json.loads(schema_file.read_text(encoding='utf-8')))
        for entity in data[data_type]:
            for error in validator.iter_errors(entity):
                errors.append(f'{data_type}: {_label(entity)}: {error.json_path}: {error.message}')

    for data_type in (FIGHTERS, ABILITIES):
        counts = Counter(entity.get('_id') for entity in data[data_type])
        for entity in data[data_type]:
            if counts[entity.get('_id')] > 1:
                errors.append(f"{data_type}: {_label(entity)}: duplicate _id {entity.get('_id')}")
    return errors
