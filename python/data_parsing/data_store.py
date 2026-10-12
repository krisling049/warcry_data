import json
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft201909Validator

from .constants import ABILITIES, FACTIONS, FIGHTERS, FILE_SUFFIXES, UNIVERSAL
from .data_loading import load_all_data, load_entities
from .models import load_json_file
from .schema_validation import SCHEMA_FILES

SCHEMAS = {data_type: json.loads(file.read_text(encoding='utf-8')) for data_type, file in SCHEMA_FILES.items()}
GRAND_ALLIANCES: list[str] = SCHEMAS[FIGHTERS]['properties']['grand_alliance']['enum']
ABILITY_COSTS: list[str] = SCHEMAS[ABILITIES]['properties']['cost']['enum']
READ_ONLY = {
    FIGHTERS: {'_id', 'warband', 'grand_alliance'},
    ABILITIES: {'_id'},
    FACTIONS: {'warband', 'grand_alliance'},
}


@dataclass(frozen=True)
class Warband:
    folder: Path

    def file(self, data_type: str) -> Path:
        return self.folder / f'{self.folder.name}{FILE_SUFFIXES[data_type]}'

    def has_faction(self) -> bool:
        return self.file(FACTIONS).is_file()


def list_warbands(src: Path) -> list[Warband]:
    folders = {f.parent for f in src.rglob('*.json') if f.name.endswith(tuple(FILE_SUFFIXES.values()))}
    return [Warband(folder) for folder in sorted(folders, key=lambda p: p.as_posix())]


def warband_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9-]+', '_', name.lower()).strip('_')


def read_entities(file: Path) -> list[dict]:
    return load_entities(file) if file.is_file() else []


def read_faction(warband: Warband) -> dict:
    return load_json_file(warband.file(FACTIONS), dict)


def write_json(file: Path, data: list | dict) -> None:
    """Write data in the source format and keep the file's line endings, so a save without changes is a no-op."""
    raw = file.read_bytes() if file.is_file() else b'\n'
    eol = '\r\n' if b'\r\n' in raw else '\n'
    text = json.dumps(data, indent=4, ensure_ascii=False) + ('\n' if raw.endswith(b'\n') else '')
    file.write_bytes(text.replace('\n', eol).encode('utf-8'))


def used_ids(src: Path) -> set[str]:
    data = load_all_data(src)
    return {e.get('_id', '') for e in data[FIGHTERS] + data[ABILITIES]}


def new_id(src: Path) -> str:
    taken = used_ids(src)
    while (candidate := uuid.uuid4().hex[:8]) in taken:
        pass
    return candidate


def subfactions(warband: Warband) -> list[str]:
    if not warband.has_faction():
        return []
    return [s.get('runemark', '') for s in read_faction(warband).get('subfactions', [])]


def ability_warbands(warband: Warband) -> list[str]:
    """The names an ability in this warband's file may have in its warband field."""
    if not warband.has_faction():
        return [UNIVERSAL]
    return [read_faction(warband).get('warband', ''), *subfactions(warband)]


def template(warband: Warband, data_type: str, entity_id: str) -> dict:
    if data_type == FIGHTERS and warband.has_faction():
        faction = read_faction(warband)
        return {'_id': entity_id, 'name': '', 'warband': faction['warband'], 'subfaction': '',
                'grand_alliance': faction['grand_alliance'], 'movement': 0, 'toughness': 0, 'wounds': 0,
                'weapons': [], 'runemarks': [], 'points': 0}
    if data_type == ABILITIES and (warband.has_faction() or warband.file(ABILITIES).is_file()):
        return {'_id': entity_id, 'name': '', 'warband': ability_warbands(warband)[0], 'cost': 'double',
                'description': '', 'runemarks': []}
    raise ValueError(f'{warband.folder.name} cannot hold new {data_type}')


def new_entity(src: Path, warband: Warband, data_type: str) -> dict:
    """An unsaved entity with a free _id."""
    return template(warband, data_type, new_id(src))


def find_entity(warband: Warband, data_type: str, entity_id: str) -> dict:
    """The stored entity, or an empty dict if there is none."""
    if data_type == FACTIONS:
        return read_faction(warband) if warband.has_faction() else {}
    return next((e for e in read_entities(warband.file(data_type)) if e.get('_id') == entity_id), {})


def merge_edit(src: Path, warband: Warband, data_type: str, entity_id: str, edited: dict) -> tuple[dict, list[str]]:
    """Put the editable fields of edited over the stored entity. Return the result and every reason not to save it."""
    original = find_entity(warband, data_type, entity_id)
    if not original:
        if data_type == FACTIONS:
            return {}, [f'{warband.folder.name} has no faction file']
        if entity_id in used_ids(src):
            return {}, [f'_id {entity_id} is used by another entity']
        try:
            original = template(warband, data_type, entity_id)
        except ValueError as e:
            return {}, [str(e)]

    entity = {**original, **{k: v for k, v in edited.items() if k not in READ_ONLY[data_type]}}
    if data_type == FIGHTERS and isinstance(entity.get('weapons'), list):
        entity['weapons'] = [dict(sorted(w.items())) if isinstance(w, dict) else w for w in entity['weapons']]
    errors = schema_errors(data_type, entity)
    if data_type != FACTIONS and not str(entity.get('name', '')).strip():
        errors.append('Name is required')
    if data_type == FIGHTERS and entity.get('subfaction') not in ['', *subfactions(warband)]:
        errors.append(f"unknown subfaction: {entity.get('subfaction')}")
    if data_type == ABILITIES and entity.get('warband') not in ability_warbands(warband):
        errors.append(f"an ability in this file cannot have warband {entity.get('warband')}")
    if data_type == FACTIONS:
        rows = entity.get('subfactions')
        kept = [s.get('runemark') for s in rows if isinstance(s, dict)] if isinstance(rows, list) else []
        used = [f.get('subfaction') for f in read_entities(warband.file(FIGHTERS))]
        used += [a.get('warband') for a in read_entities(warband.file(ABILITIES))]
        errors += [f'subfaction {name} is in use; rename or remove it in the JSON files'
                   for name in subfactions(warband) if name and name in used and name not in kept]
    return entity, errors


def write_entity(warband: Warband, data_type: str, entity: dict) -> None:
    if data_type == FACTIONS:
        write_json(warband.file(FACTIONS), entity)
    else:
        save_entity(warband.file(data_type), entity)


def duplicate_entity(src: Path, warband: Warband, data_type: str, entity_id: str) -> dict:
    """Save a copy of the entity with a new _id and return it."""
    original = find_entity(warband, data_type, entity_id)
    if data_type == FACTIONS or not original:
        raise ValueError(f'no {data_type} with _id {entity_id} in {warband.folder.name}')
    copy = {**original, '_id': new_id(src), 'name': f"{original.get('name', '')} (copy)"}
    save_entity(warband.file(data_type), copy)
    return copy


def schema_errors(data_type: str, entity: dict) -> list[str]:
    validator = Draft201909Validator(SCHEMAS[data_type])
    return [f'{error.json_path}: {error.message}' for error in validator.iter_errors(entity)]


def save_entity(file: Path, entity: dict) -> None:
    """Replace the entity with the same _id in file, or append it."""
    entities = read_entities(file)
    index = next((i for i, e in enumerate(entities) if e.get('_id') == entity['_id']), len(entities))
    entities[index:index + 1] = [entity]
    write_json(file, entities)


def delete_entity(file: Path, entity_id: str) -> None:
    write_json(file, [e for e in read_entities(file) if e.get('_id') != entity_id])


def create_warband(src: Path, grand_alliance: str, name: str) -> Warband:
    if grand_alliance not in GRAND_ALLIANCES:
        raise ValueError(f'unknown grand alliance: {grand_alliance}')
    slug = warband_slug(name)
    if not re.search('[a-z0-9]', slug):
        raise ValueError(f'warband name has no letters or digits: {name!r}')
    if any(name in ability_warbands(w) for w in list_warbands(src) if w.has_faction()):
        raise ValueError(f'warband or subfaction already exists: {name}')

    warband = Warband(src / grand_alliance / slug)
    if warband.folder.exists():
        raise ValueError(f'folder already exists: {warband.folder}')
    warband.folder.mkdir(parents=True)
    write_json(warband.file(FACTIONS), {
        'grand_alliance': grand_alliance,
        'warband': name,
        'bladeborn': False,
        'heroes_all': False,
        'subfactions': [],
        'singleton': False,
    })
    write_json(warband.file(FIGHTERS), [])
    write_json(warband.file(ABILITIES), [])
    return warband


def delete_warband(warband: Warband) -> None:
    shutil.rmtree(warband.folder)
