import json
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from data_parsing.data_loading import load_all_data
from data_parsing.models import LOCALISATION_DATA, PROJECT_DATA, PROJECT_ROOT
from data_parsing.schema_validation import validate_data
from data_parsing.warband_pipeline import WarbandDataPipeline

WARBAND = Path('order', 'twistweald')


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """A copy of one real warband plus universal abilities, safe to break."""
    dst = tmp_path / 'data'
    shutil.copytree(PROJECT_DATA / WARBAND, dst / WARBAND)
    shutil.copytree(PROJECT_DATA / 'universal', dst / 'universal')
    return dst


def read(file: Path) -> list | dict:
    return json.loads(file.read_text(encoding='utf-8'))


def write(file: Path, data: list | dict) -> None:
    file.write_text(json.dumps(data, indent=4), encoding='utf-8')


def fighters_file(data_dir: Path) -> Path:
    return data_dir / WARBAND / 'twistweald_fighters.json'


def test_repo_data_is_valid() -> None:
    assert validate_data(load_all_data(PROJECT_DATA)) == []


def test_fixture_is_valid(data_dir: Path) -> None:
    assert validate_data(load_all_data(data_dir)) == []


def test_every_schema_error_is_reported(data_dir: Path) -> None:
    fighters = read(fighters_file(data_dir))
    del fighters[0]['points']
    del fighters[1]['points']
    write(fighters_file(data_dir), fighters)

    errors = validate_data(load_all_data(data_dir))

    assert len(errors) == 2
    assert fighters[0]['name'] in errors[0] and fighters[1]['name'] in errors[1]


def test_duplicate_id_is_rejected(data_dir: Path) -> None:
    fighters = read(fighters_file(data_dir))
    fighters[1]['_id'] = fighters[0]['_id']
    write(fighters_file(data_dir), fighters)

    errors = validate_data(load_all_data(data_dir))

    assert any('duplicate _id' in e for e in errors)
    with pytest.raises(ValueError, match='duplicate _id'):
        WarbandDataPipeline(src=data_dir)


@pytest.mark.parametrize('placeholder', ['PLACEHOLDER', 'XXXXXX', 'placeholder1'])
def test_placeholder_id_is_rejected(data_dir: Path, placeholder: str) -> None:
    abilities_file = data_dir / WARBAND / 'twistweald_abilities.json'
    abilities = read(abilities_file)
    abilities[0]['_id'] = placeholder
    write(abilities_file, abilities)

    errors = validate_data(load_all_data(data_dir))

    assert errors
    assert all(e.startswith(f"abilities: Twistweald/{abilities[0]['name']}: $['_id']: ") for e in errors)


def test_id_with_trailing_newline_is_rejected(data_dir: Path) -> None:
    fighters = read(fighters_file(data_dir))
    fighters[0]['_id'] += '\n'
    write(fighters_file(data_dir), fighters)

    errors = validate_data(load_all_data(data_dir))

    assert errors and all("$['_id']" in e for e in errors)


@pytest.mark.parametrize('item', [None, [], 'text'])
def test_non_object_item_is_rejected(data_dir: Path, item: object) -> None:
    fighters = read(fighters_file(data_dir))
    fighters.append(item)
    write(fighters_file(data_dir), fighters)

    with pytest.raises(ValueError, match=r'twistweald_fighters\.json: item \d+ is a JSON'):
        load_all_data(data_dir)


def test_bad_faction_is_reported_not_crashed(data_dir: Path) -> None:
    faction_file = data_dir / WARBAND / 'twistweald_faction.json'
    faction = read(faction_file)
    del faction['warband']
    write(faction_file, faction)

    errors = validate_data(load_all_data(data_dir))

    assert any(e.startswith('factions:') and 'warband' in e for e in errors)


def test_validation_makes_no_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object) -> None:
        raise AssertionError('validation opened a network connection')

    monkeypatch.setattr(socket.socket, 'connect', refuse)
    assert validate_data(load_all_data(PROJECT_DATA)) == []


def test_files_load_in_sorted_order(data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.copytree(PROJECT_DATA / 'order' / 'blacktalons', data_dir / 'order' / 'blacktalons')
    real_rglob = Path.rglob
    monkeypatch.setattr(Path, 'rglob', lambda self, pattern: reversed(list(real_rglob(self, pattern))))

    warbands = [f['warband'] for f in load_all_data(data_dir)['fighters']]

    assert warbands.index('Blacktalons') < warbands.index('Twistweald')


def test_non_utf8_file_is_rejected(data_dir: Path) -> None:
    file = fighters_file(data_dir)
    file.write_bytes(file.read_bytes().replace(b'"name": "', b'"name": "\x92', 1))

    with pytest.raises(ValueError, match='twistweald_fighters.json'):
        load_all_data(data_dir)


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(PROJECT_ROOT / 'python' / script), *args],
                          capture_output=True, text=True)


def test_validation_cli_uses_data_argument(data_dir: Path) -> None:
    assert run_script('validation.py', '--data', str(data_dir)).returncode == 0

    fighters = read(fighters_file(data_dir))
    fighters[1]['_id'] = fighters[0]['_id']
    write(fighters_file(data_dir), fighters)
    assert run_script('validation.py', '--data', str(data_dir)).returncode == 1


def test_validation_cli_rejects_missing_folder(tmp_path: Path) -> None:
    result = run_script('validation.py', '--data', str(tmp_path / 'missing'))
    assert result.returncode != 0
    assert 'data folder not found' in result.stderr


def test_export_does_not_depend_on_filesystem_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    WarbandDataPipeline().export_all(tmp_path / 'a')
    real_rglob = Path.rglob
    monkeypatch.setattr(Path, 'rglob', lambda self, pattern: reversed(list(real_rglob(self, pattern))))
    WarbandDataPipeline().export_all(tmp_path / 'b')

    files = sorted(p.relative_to(tmp_path / 'a') for p in (tmp_path / 'a').rglob('*') if p.is_file())
    assert len(files) == 9
    for file in files:
        assert (tmp_path / 'a' / file).read_bytes() == (tmp_path / 'b' / file).read_bytes(), file


def test_index_links_exactly_the_published_files(tmp_path: Path) -> None:
    (tmp_path / 'stale.json').write_text('[]', encoding='utf-8')
    WarbandDataPipeline().export_all(tmp_path)

    hrefs = re.findall(r'<a href="([^"]+)">', (tmp_path / 'index.html').read_text(encoding='utf-8'))
    written = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*') if p.is_file()}

    assert sorted(h for h in hrefs if not h.startswith('https://')) == sorted(
        written - {'index.html', 'stale.json'})


def test_tts_ability_references_resolve(tmp_path: Path) -> None:
    WarbandDataPipeline().export_all(tmp_path)
    ability_ids = {a['_id'] for a in read(tmp_path / 'abilities_battletraits.json')}

    for fighter in read(tmp_path / 'fighters_tts.json'):
        assert {a['_id'] for a in fighter['abilities']} <= ability_ids, fighter['name']


@pytest.mark.parametrize('loc_file', sorted(LOCALISATION_DATA.glob('*.json')), ids=lambda p: p.stem)
def test_localisation_holds_only_translations(loc_file: Path) -> None:
    abilities = {a['_id']: a for a in load_all_data(PROJECT_DATA)['abilities']}

    for _id, fields in read(loc_file).items():
        assert _id in abilities, _id
        assert fields.get('description') != abilities[_id]['description'], f'{_id} is a copy of the English text'
        for field, text in fields.items():
            assert 'â€' not in text and 'Ã' not in text, f'{_id}.{field} has mojibake'
