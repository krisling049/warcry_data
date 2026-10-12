import json
import shutil
import socket
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from data_parsing import data_store
from data_parsing.constants import ABILITIES, FACTIONS, FIGHTERS
from data_parsing.data_loading import load_all_data
from data_parsing.data_store import Warband
from data_parsing.models import PROJECT_DATA
from data_parsing.schema_validation import validate_data
from data_server import Handler, Server

TWISTWEALD = Path('order', 'twistweald')
WARBAND = TWISTWEALD.as_posix()


@dataclass
class Reply:
    status: int
    body: dict


@pytest.fixture
def src(tmp_path: Path) -> Path:
    dst = tmp_path / 'data'
    shutil.copytree(PROJECT_DATA / TWISTWEALD, dst / TWISTWEALD)
    shutil.copytree(PROJECT_DATA / 'universal', dst / 'universal')
    return dst


@pytest.fixture
def base_url(src: Path) -> Iterator[str]:
    server = Server(src, 0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    thread.join()
    server.server_close()


def request(url: str, method: str = 'GET', body: dict = {}, content_type: str = 'application/json',
            host: str = '') -> Reply:
    data = None if method == 'GET' else json.dumps(body).encode('utf-8')
    headers = {'Content-Type': content_type, **({'Host': host} if host else {})}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, headers, method=method)) as response:
            return Reply(response.status, json.loads(response.read()))
    except urllib.error.HTTPError as e:
        return Reply(e.code, json.loads(e.read()))


def fighters(src: Path) -> list[dict]:
    return data_store.read_entities(Warband(src / TWISTWEALD).file(FIGHTERS))


def test_tree_lists_warbands(base_url: str) -> None:
    tree = request(f'{base_url}/api/tree').body

    assert [w['id'] for w in tree['warbands']] == [WARBAND, 'universal']
    assert tree['warbands'][0]['group'] == 'order'
    assert set(tree['warbands'][1]['lists']) == {ABILITIES}
    assert tree['problems'] == []


def test_tree_items_carry_their_subfaction(base_url: str, src: Path) -> None:
    shutil.copytree(PROJECT_DATA / 'death' / 'ossiarch_bonereapers', src / 'death' / 'ossiarch_bonereapers')

    tree = request(f'{base_url}/api/tree').body

    lists = next(w for w in tree['warbands'] if w['id'] == 'death/ossiarch_bonereapers')['lists']
    for data_type in (FIGHTERS, ABILITIES):
        assert "Kainan's Reapers" in {item['subfaction'] for item in lists[data_type]}


def test_unchanged_put_keeps_every_byte(base_url: str, src: Path) -> None:
    before = {file: file.read_bytes() for file in src.rglob('*.json')}
    tree = request(f'{base_url}/api/tree').body

    for warband in tree['warbands']:
        for data_type, items in warband['lists'].items():
            for item in items:
                url = f"{base_url}/api/entity?warband={warband['id']}&type={data_type}&id={item['_id']}"
                assert request(url, 'PUT', request(url).body).status == 200
        if warband['has_faction']:
            url = f"{base_url}/api/entity?warband={warband['id']}&type=factions"
            assert request(url, 'PUT', request(url).body).status == 200

    assert {file: file.read_bytes() for file in src.rglob('*.json')} == before


def test_put_merges_and_protects_fields(base_url: str, src: Path) -> None:
    fighter = fighters(src)[0]
    url = f"{base_url}/api/entity?warband={WARBAND}&type=fighters&id={fighter['_id']}"

    reply = request(url, 'PUT', {'points': 321, 'warband': 'Other', '_id': 'zzzzzzzz'})

    assert reply.status == 200
    assert fighters(src)[0] == {**fighter, 'points': 321}


def test_put_reports_every_error(base_url: str, src: Path) -> None:
    fighter = fighters(src)[0]
    url = f"{base_url}/api/entity?warband={WARBAND}&type=fighters&id={fighter['_id']}"

    reply = request(url, 'PUT', {'points': 'abc', 'name': ' ', 'subfaction': 'Nobody'})

    assert reply.status == 400
    assert reply.body['errors'] == ["$.points: 'abc' is not of type 'integer'", 'Name is required',
                                    'unknown subfaction: Nobody']
    assert fighters(src)[0] == fighter


def test_new_fighter_is_saved_on_put(base_url: str, src: Path) -> None:
    new = request(f'{base_url}/api/new?warband={WARBAND}&type=fighters', 'POST').body
    assert new['_id'] not in {f['_id'] for f in fighters(src)}

    weapon = {'runemark': 'axe', 'strength': 4, 'attacks': 3, 'dmg_hit': 1, 'dmg_crit': 3, 'min_range': 0,
              'max_range': 1}
    url = f"{base_url}/api/entity?warband={WARBAND}&type=fighters&id={new['_id']}"
    assert request(url, 'PUT', {'name': 'Test Fighter', 'weapons': [weapon]}).status == 200

    saved = fighters(src)[-1]
    assert saved['name'] == 'Test Fighter' and list(saved) == list(new)
    assert list(saved['weapons'][0]) == sorted(weapon)
    assert validate_data(load_all_data(src)) == []


def test_put_rejects_id_used_elsewhere(base_url: str, src: Path) -> None:
    ability_id = data_store.read_entities(Warband(src / 'universal').file(ABILITIES))[0]['_id']
    url = f'{base_url}/api/entity?warband={WARBAND}&type=fighters&id={ability_id}'

    reply = request(url, 'PUT', {'name': 'Clash'})

    assert reply.status == 400 and 'is used by another entity' in reply.body['errors'][0]


def test_duplicate_and_delete(base_url: str, src: Path) -> None:
    original = fighters(src)
    copy = request(f"{base_url}/api/duplicate?warband={WARBAND}&type=fighters&id={original[0]['_id']}", 'POST').body
    assert fighters(src) == [*original, copy]
    assert copy['name'] == f"{original[0]['name']} (copy)"

    url = f"{base_url}/api/entity?warband={WARBAND}&type=fighters&id={copy['_id']}"
    assert request(url, 'DELETE').status == 200
    assert fighters(src) == original
    assert request(url, 'DELETE').status == 404


def test_create_and_delete_warband(base_url: str, src: Path) -> None:
    reply = request(f'{base_url}/api/warband', 'POST', {'grand_alliance': 'chaos', 'name': 'Test Band'})
    assert reply.body == {'id': 'chaos/test_band'}
    assert validate_data(load_all_data(src)) == []
    assert request(f'{base_url}/api/warband', 'POST', {'grand_alliance': 'chaos', 'name': 'Test Band'}).status == 400

    assert request(f'{base_url}/api/warband?warband=chaos/test_band', 'DELETE').status == 200
    assert not (src / 'chaos' / 'test_band').exists()


@pytest.mark.parametrize('warband', ['../data/order/twistweald', 'order', 'order/twistweald/..', ''])
def test_unknown_warband_is_not_found(base_url: str, warband: str) -> None:
    assert request(f'{base_url}/api/warband?warband={warband}', 'DELETE').status == 404


def test_write_needs_json_content_type(base_url: str, src: Path) -> None:
    reply = request(f'{base_url}/api/warband?warband={WARBAND}', 'DELETE', content_type='text/plain')

    assert reply.status == 415
    assert (src / TWISTWEALD).exists()


def test_foreign_host_is_forbidden(base_url: str) -> None:
    assert request(f'{base_url}/api/tree', host='evil.example:80').status == 403


def test_page_is_served(base_url: str) -> None:
    with urllib.request.urlopen(f'{base_url}/') as response:
        assert b'<script src="app.js">' in response.read()
    with urllib.request.urlopen(f'{base_url}/app.js') as response:
        assert response.headers.get_content_type() == 'text/javascript'


def raw(base_url: str, data: bytes) -> bytes:
    with socket.create_connection(('127.0.0.1', int(base_url.rsplit(':', 1)[1])), timeout=5) as sock:
        sock.sendall(data)
        return b''.join(iter(lambda: sock.recv(65536), b''))


def test_page_cannot_be_framed(base_url: str) -> None:
    with urllib.request.urlopen(f'{base_url}/') as response:
        assert response.headers['Content-Security-Policy'] == "frame-ancestors 'none'"


@pytest.mark.parametrize('length, status', [(b'abc', b'400'), (b'-1', b'400'), (b'1000000000000000', b'413')])
def test_bad_content_length_is_rejected(base_url: str, length: bytes, status: bytes) -> None:
    reply = raw(base_url, b'POST /api/warband HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n'
                          b'Content-Length: ' + length + b'\r\n\r\n')

    assert reply.startswith(b'HTTP/1.0 ' + status)


def test_deeply_nested_body_is_rejected(base_url: str) -> None:
    body = b'[' * 200_000
    reply = raw(base_url, b'POST /api/warband HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n'
                          b'Content-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body)

    assert reply.startswith(b'HTTP/1.0 400')


def test_idle_connection_does_not_block_the_server(base_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    assert Handler.timeout is not None
    monkeypatch.setattr(Handler, 'timeout', 0.5)
    with socket.create_connection(('127.0.0.1', int(base_url.rsplit(':', 1)[1]))):
        with urllib.request.urlopen(f'{base_url}/api/meta', timeout=5) as response:
            assert response.status == 200


def test_second_server_on_the_same_port_fails(base_url: str, src: Path) -> None:
    with pytest.raises(OSError):
        Server(src, int(base_url.rsplit(':', 1)[1]))


def test_bad_faction_file_does_not_hide_other_warbands(base_url: str, src: Path) -> None:
    file = Warband(src / TWISTWEALD).file(FACTIONS)
    data_store.write_json(file, {**data_store.read_faction(Warband(src / TWISTWEALD)), 'subfactions': ['Foo']})

    tree = request(f'{base_url}/api/tree').body

    assert [w['id'] for w in tree['warbands']] == ['universal']
    assert len(tree['problems']) == 1 and 'twistweald' in tree['problems'][0]


def test_unexpected_error_gets_a_json_reply(base_url: str, src: Path) -> None:
    faction = data_store.read_faction(Warband(src / TWISTWEALD))
    del faction['warband']
    data_store.write_json(Warband(src / TWISTWEALD).file(FACTIONS), faction)

    reply = request(f'{base_url}/api/new?warband={WARBAND}&type=fighters', 'POST')

    assert reply.status == 500 and reply.body['errors'] == ["KeyError: 'warband'"]


def test_faction_save_keeps_subfactions_in_use(base_url: str, src: Path) -> None:
    shutil.copytree(PROJECT_DATA / 'death' / 'ossiarch_bonereapers', src / 'death' / 'ossiarch_bonereapers')
    file = Warband(src / 'death' / 'ossiarch_bonereapers').file(FACTIONS)
    before = file.read_bytes()
    faction = json.loads(before)
    kept = [s for s in faction['subfactions'] if s['runemark'] != "Kainan's Reapers"]

    reply = request(f'{base_url}/api/entity?warband=death/ossiarch_bonereapers&type=factions', 'PUT',
                    {'subfactions': kept})

    assert reply.status == 400
    assert reply.body['errors'] == ["subfaction Kainan's Reapers is in use; rename or remove it in the JSON files"]
    assert file.read_bytes() == before


def test_validate(base_url: str, src: Path) -> None:
    assert request(f'{base_url}/api/validate').body == {'errors': []}

    data_store.save_entity(Warband(src / TWISTWEALD).file(FIGHTERS), {**fighters(src)[0], 'points': 'x'})

    assert len(request(f'{base_url}/api/validate').body['errors']) == 1
