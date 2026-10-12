import json
import re
import shutil
from pathlib import Path

import pytest

from data_parsing import data_store
from data_parsing.constants import ABILITIES, FACTIONS, FIGHTERS
from data_parsing.data_loading import load_all_data
from data_parsing.data_store import Warband
from data_parsing.models import PROJECT_DATA
from data_parsing.schema_validation import validate_data

TWISTWEALD = Path('order', 'twistweald')


@pytest.fixture
def src(tmp_path: Path) -> Path:
    dst = tmp_path / 'data'
    shutil.copytree(PROJECT_DATA / TWISTWEALD, dst / TWISTWEALD)
    shutil.copytree(PROJECT_DATA / 'universal', dst / 'universal')
    return dst


def test_list_warbands_finds_every_data_folder(src: Path) -> None:
    assert data_store.list_warbands(src) == [Warband(src / TWISTWEALD), Warband(src / 'universal')]


def test_unchanged_write_keeps_every_byte(src: Path) -> None:
    for file in src.rglob('*.json'):
        original = file.read_bytes()
        data_store.write_json(file, json.loads(original))
        assert file.read_bytes() == original, file


@pytest.mark.parametrize('ending', [b'\r\n', b''])
def test_write_keeps_line_endings(tmp_path: Path, ending: bytes) -> None:
    file = tmp_path / 'x.json'
    file.write_bytes(b'[\r\n    1\r\n]' + ending)

    data_store.write_json(file, [2])

    assert file.read_bytes() == b'[\r\n    2\r\n]' + ending


def test_save_entity_replaces_in_place_and_appends(src: Path) -> None:
    file = Warband(src / TWISTWEALD).file(FIGHTERS)
    fighters = data_store.read_entities(file)

    data_store.save_entity(file, {**fighters[1], 'points': 999})
    data_store.save_entity(file, {**fighters[0], '_id': 'zzzzzzzz'})

    saved = data_store.read_entities(file)
    assert [f['_id'] for f in saved] == [f['_id'] for f in fighters] + ['zzzzzzzz']
    assert saved[1]['points'] == 999


def test_delete_entity(src: Path) -> None:
    file = Warband(src / TWISTWEALD).file(ABILITIES)
    abilities = data_store.read_entities(file)

    data_store.delete_entity(file, abilities[0]['_id'])

    assert data_store.read_entities(file) == abilities[1:]


def test_new_id_is_valid_and_unused(src: Path) -> None:
    data = load_all_data(src)
    entity_id = data_store.new_id(src)

    assert re.fullmatch(r'[0-9a-z]{8}', entity_id)
    assert entity_id not in {e['_id'] for e in data[FIGHTERS] + data[ABILITIES]}


def test_schema_errors(src: Path) -> None:
    fighter = data_store.read_entities(Warband(src / TWISTWEALD).file(FIGHTERS))[0]

    assert data_store.schema_errors(FIGHTERS, fighter) == []
    assert data_store.schema_errors(FIGHTERS, {**fighter, 'points': '1'}) == ["$.points: '1' is not of type 'integer'"]


def test_slug_matches_every_existing_folder() -> None:
    for warband in data_store.list_warbands(PROJECT_DATA):
        if warband.has_faction():
            assert data_store.warband_slug(data_store.read_faction(warband)['warband']) == warband.folder.name


def test_create_warband_makes_valid_files(src: Path) -> None:
    warband = data_store.create_warband(src, 'chaos', 'Blades of Khorne: Test')

    assert warband.folder == src / 'chaos' / 'blades_of_khorne_test'
    assert data_store.read_faction(warband)['warband'] == 'Blades of Khorne: Test'
    assert data_store.read_entities(warband.file(FIGHTERS)) == []
    assert validate_data(load_all_data(src)) == []


@pytest.mark.parametrize('alliance, name, message', [
    ('order', 'Twistweald', 'already exists: Twistweald'),
    ('elves', 'Test', 'unknown grand alliance'),
    ('order', ': !', 'no letters or digits'),
    ('order', '-', 'no letters or digits'),
])
def test_create_warband_rejects_bad_input(src: Path, alliance: str, name: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        data_store.create_warband(src, alliance, name)


def test_create_warband_rejects_a_subfaction_name(src: Path) -> None:
    shutil.copytree(PROJECT_DATA / 'death' / 'ossiarch_bonereapers', src / 'death' / 'ossiarch_bonereapers')

    with pytest.raises(ValueError, match="warband or subfaction already exists: Kainan's Reapers"):
        data_store.create_warband(src, 'death', "Kainan's Reapers")


def test_delete_warband(src: Path) -> None:
    warband = Warband(src / TWISTWEALD)

    data_store.delete_warband(warband)

    assert not warband.folder.exists()
    assert not load_all_data(src)[FACTIONS]


def test_merge_edit_keeps_unknown_keys_and_order(src: Path) -> None:
    shutil.copytree(PROJECT_DATA / 'order' / 'order', src / 'order' / 'order')
    warband = Warband(src / 'order' / 'order')
    ability = next(a for a in data_store.read_entities(warband.file(ABILITIES)) if 'monster' in a)

    entity, errors = data_store.merge_edit(src, warband, ABILITIES, ability['_id'], {'name': 'X', '_id': 'zzzzzzzz'})

    assert errors == []
    assert entity == {**ability, 'name': 'X'} and list(entity) == list(ability)


def test_merge_edit_sorts_weapon_keys(src: Path) -> None:
    warband = Warband(src / TWISTWEALD)
    fighter = data_store.read_entities(warband.file(FIGHTERS))[0]
    weapons = [dict(reversed(list(w.items()))) for w in fighter['weapons']]

    entity, _ = data_store.merge_edit(src, warband, FIGHTERS, fighter['_id'], {'weapons': weapons})

    assert [list(w) for w in entity['weapons']] == [list(w) for w in fighter['weapons']]


def test_merge_edit_removes_a_subfaction_with_no_runemark(src: Path) -> None:
    warband = Warband(src / TWISTWEALD)
    faction = data_store.read_faction(warband)
    row = {'runemark': '', 'bladeborn': False, 'heroes_all': False}
    data_store.write_json(warband.file(FACTIONS), {**faction, 'subfactions': [row]})

    _, errors = data_store.merge_edit(src, warband, FACTIONS, '', {'subfactions': []})

    assert errors == []


def test_ability_warbands(src: Path) -> None:
    assert data_store.ability_warbands(Warband(src / TWISTWEALD)) == ['Twistweald']
    assert data_store.ability_warbands(Warband(src / 'universal')) == ['universal']
    assert 'Kainan\'s Reapers' in data_store.ability_warbands(Warband(PROJECT_DATA / 'death' / 'ossiarch_bonereapers'))


def test_universal_cannot_hold_fighters(src: Path) -> None:
    with pytest.raises(ValueError, match='cannot hold new fighters'):
        data_store.new_entity(src, Warband(src / 'universal'), FIGHTERS)
    assert data_store.new_entity(src, Warband(src / 'universal'), ABILITIES)['warband'] == 'universal'


def test_duplicate_entity_saves_a_copy(src: Path) -> None:
    file = Warband(src / TWISTWEALD).file(ABILITIES)
    original = data_store.read_entities(file)[0]

    copy = data_store.duplicate_entity(src, Warband(src / TWISTWEALD), ABILITIES, original['_id'])

    assert data_store.read_entities(file)[-1] == copy
    assert copy == {**original, '_id': copy['_id'], 'name': f"{original['name']} (copy)"}
    assert validate_data(load_all_data(src)) == []