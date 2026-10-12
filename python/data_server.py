import argparse
import json
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from data_parsing import data_store
from data_parsing.constants import ABILITIES, FACTIONS, FIGHTERS
from data_parsing.data_loading import load_all_data
from data_parsing.data_store import ABILITY_COSTS, GRAND_ALLIANCES, Warband
from data_parsing.models import PROJECT_DATA
from data_parsing.schema_validation import validate_data

WEB = Path(__file__).parent / 'web'
STATIC = {
    '/': ('index.html', 'text/html'),
    '/app.js': ('app.js', 'text/javascript'),
    '/style.css': ('style.css', 'text/css'),
}
LOCAL_HOSTS = {'127.0.0.1', 'localhost'}
Query = dict[str, str]
Reply = tuple[HTTPStatus, dict]


@dataclass
class TypedArgs:
    data: Path
    port: int


class NotFound(Exception):
    pass


class Server(HTTPServer):
    """Serves the editor page and its JSON API on the loopback interface only."""

    def __init__(self, src: Path, port: int) -> None:
        super().__init__(('127.0.0.1', port), Handler)
        self.src = src


def summary(src: Path, warband: Warband) -> dict:
    rel = warband.folder.relative_to(src)
    has_faction = warband.has_faction()
    lists = {}
    for data_type in (FIGHTERS, ABILITIES):
        if has_faction or warband.file(data_type).is_file():
            lists[data_type] = [{
                '_id': e.get('_id', ''),
                'name': e.get('name', ''),
                'detail': f"{e.get('points')} pts" if data_type == FIGHTERS else e.get('cost', ''),
                'subfaction': e.get('subfaction', '') if data_type == FIGHTERS else e.get('warband', ''),
            } for e in data_store.read_entities(warband.file(data_type))]
    return {
        'id': rel.as_posix(),
        'group': rel.parent.as_posix() if rel.parent != Path('.') else '',
        'name': data_store.read_faction(warband).get('warband', rel.name) if has_faction else rel.name,
        'has_faction': has_faction,
        'subfactions': data_store.subfactions(warband),
        'ability_warbands': data_store.ability_warbands(warband),
        'lists': lists,
    }


class Handler(BaseHTTPRequestHandler):
    server: Server

    def do_GET(self) -> None:
        self.dispatch('GET')

    def do_POST(self) -> None:
        self.dispatch('POST')

    def do_PUT(self) -> None:
        self.dispatch('PUT')

    def do_DELETE(self) -> None:
        self.dispatch('DELETE')

    def dispatch(self, method: str) -> None:
        # Unread request bytes make Windows reset the connection before the client reads the reply.
        self.raw_body = self.rfile.read(int(self.headers.get('Content-Length') or 0))
        url = urlsplit(self.path)
        host = (self.headers.get('Host') or '').rsplit(':', 1)[0]
        if host not in LOCAL_HOSTS:
            self.send_json(HTTPStatus.FORBIDDEN, {'errors': [f'unknown host: {host}']})
            return
        if method == 'GET' and url.path in STATIC:
            self.send_static(*STATIC[url.path])
            return
        # A JSON content type makes a browser ask for CORS approval, which this server never gives.
        if method != 'GET' and self.headers.get_content_type() != 'application/json':
            self.send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {'errors': ['send application/json']})
            return
        route = ROUTES.get((method, url.path))
        if route is None:
            self.send_json(HTTPStatus.NOT_FOUND, {'errors': [f'no route: {method} {url.path}']})
            return
        query = {key: values[0] for key, values in parse_qs(url.query).items()}
        try:
            status, payload = route(self, query)
        except NotFound as e:
            status, payload = HTTPStatus.NOT_FOUND, {'errors': [str(e)]}
        except ValueError as e:
            status, payload = HTTPStatus.BAD_REQUEST, {'errors': [str(e)]}
        self.send_json(status, payload)

    def send_static(self, name: str, content_type: str) -> None:
        self.send_body(HTTPStatus.OK, (WEB / name).read_bytes(), f'{content_type}; charset=utf-8')

    def send_json(self, status: HTTPStatus, payload: dict) -> None:
        self.send_body(status, json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                       'application/json; charset=utf-8')

    def send_body(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def body(self) -> dict:
        try:
            content = json.loads(self.raw_body or b'{}')
        except json.JSONDecodeError as e:
            raise ValueError(f'request body is not JSON: {e}') from e
        if not isinstance(content, dict):
            raise ValueError('request body must be a JSON object')
        return content

    def warband(self, query: Query) -> Warband:
        warbands = {w.folder.relative_to(self.server.src).as_posix(): w
                    for w in data_store.list_warbands(self.server.src)}
        if query.get('warband', '') not in warbands:
            raise NotFound(f"unknown warband: {query.get('warband', '')}")
        return warbands[query['warband']]

    def data_type(self, query: Query, allowed: tuple[str, ...] = (FIGHTERS, ABILITIES, FACTIONS)) -> str:
        if query.get('type', '') not in allowed:
            raise ValueError(f"type must be one of {', '.join(allowed)}")
        return query['type']

    def tree(self, _query: Query) -> Reply:
        warbands, problems = [], []
        for warband in data_store.list_warbands(self.server.src):
            try:
                warbands.append(summary(self.server.src, warband))
            except ValueError as e:
                problems.append(f'{warband.folder}: {e}')
        return HTTPStatus.OK, {'warbands': warbands, 'problems': problems}

    def meta(self, _query: Query) -> Reply:
        return HTTPStatus.OK, {'grand_alliances': GRAND_ALLIANCES, 'ability_costs': ABILITY_COSTS,
                               'data': str(self.server.src)}

    def get_entity(self, query: Query) -> Reply:
        entity = data_store.find_entity(self.warband(query), self.data_type(query), query.get('id', ''))
        if not entity:
            raise NotFound(f"no {query['type']} with _id {query.get('id', '')}")
        return HTTPStatus.OK, entity

    def put_entity(self, query: Query) -> Reply:
        warband, data_type = self.warband(query), self.data_type(query)
        entity, errors = data_store.merge_edit(self.server.src, warband, data_type, query.get('id', ''), self.body())
        if errors:
            return HTTPStatus.BAD_REQUEST, {'errors': errors}
        data_store.write_entity(warband, data_type, entity)
        return HTTPStatus.OK, entity

    def delete_entity(self, query: Query) -> Reply:
        warband, data_type = self.warband(query), self.data_type(query, (FIGHTERS, ABILITIES))
        if not data_store.find_entity(warband, data_type, query.get('id', '')):
            raise NotFound(f"no {data_type} with _id {query.get('id', '')}")
        data_store.delete_entity(warband.file(data_type), query['id'])
        return HTTPStatus.OK, {'deleted': query['id']}

    def new_entity(self, query: Query) -> Reply:
        warband, data_type = self.warband(query), self.data_type(query, (FIGHTERS, ABILITIES))
        return HTTPStatus.OK, data_store.new_entity(self.server.src, warband, data_type)

    def duplicate(self, query: Query) -> Reply:
        warband, data_type = self.warband(query), self.data_type(query, (FIGHTERS, ABILITIES))
        return HTTPStatus.OK, data_store.duplicate_entity(self.server.src, warband, data_type, query.get('id', ''))

    def create_warband(self, _query: Query) -> Reply:
        body = self.body()
        warband = data_store.create_warband(self.server.src, str(body.get('grand_alliance', '')),
                                            str(body.get('name', '')).strip())
        return HTTPStatus.OK, {'id': warband.folder.relative_to(self.server.src).as_posix()}

    def delete_warband(self, query: Query) -> Reply:
        warband = self.warband(query)
        if not warband.has_faction():
            raise ValueError(f"{query['warband']} has no faction file")
        data_store.delete_warband(warband)
        return HTTPStatus.OK, {'deleted': query['warband']}

    def validate(self, _query: Query) -> Reply:
        try:
            return HTTPStatus.OK, {'errors': validate_data(load_all_data(self.server.src))}
        except ValueError as e:
            return HTTPStatus.OK, {'errors': [str(e)]}


ROUTES: dict[tuple[str, str], Callable[[Handler, Query], Reply]] = {
    ('GET', '/api/tree'): Handler.tree,
    ('GET', '/api/meta'): Handler.meta,
    ('GET', '/api/entity'): Handler.get_entity,
    ('PUT', '/api/entity'): Handler.put_entity,
    ('DELETE', '/api/entity'): Handler.delete_entity,
    ('POST', '/api/new'): Handler.new_entity,
    ('POST', '/api/duplicate'): Handler.duplicate,
    ('POST', '/api/warband'): Handler.create_warband,
    ('DELETE', '/api/warband'): Handler.delete_warband,
    ('GET', '/api/validate'): Handler.validate,
}


def parse_args() -> TypedArgs:
    parser = argparse.ArgumentParser(description='Serve a local web page to create, edit and delete source data.')
    parser.add_argument('--data', type=Path, default=PROJECT_DATA, help='path to the source data folder')
    parser.add_argument('--port', type=int, default=4424, help='port on 127.0.0.1 (default: 4424)')
    return TypedArgs(**vars(parser.parse_args()))


if __name__ == '__main__':
    args = parse_args()
    if not args.data.is_dir():
        raise SystemExit(f'data folder not found: {args.data}')
    server = Server(args.data, args.port)
    print(f'Editing {args.data} at http://127.0.0.1:{server.server_port}/ - press Ctrl+C to stop', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
