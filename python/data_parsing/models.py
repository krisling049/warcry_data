import json
from pathlib import Path
from typing import List, Dict, Union

import jsonschema

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_DATA = Path(PROJECT_ROOT, 'data')
DIST = Path(PROJECT_ROOT, 'docs')
LOCAL_DATA = Path(PROJECT_ROOT, 'local', 'data')
LOCALISATION_DATA = Path(PROJECT_ROOT, 'localisation')


def sanitise_filename(filename: str) -> str:
    for illegal_char in r'\\/:*?\"<>|':
        filename = str(filename).replace(illegal_char, '')

    return filename.lower().replace(' ', '_')


def write_data_json(dst: Path, data: Union[List, Dict], encoding: str = 'latin-1'):
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
        # self.validate_data()

    @classmethod
    def load_data(cls):
        raise NotImplementedError('class requires a load_data class method')

    @classmethod
    def write_to_disk(cls):
        raise NotImplementedError('class requires a write_to_disk class method')

    @classmethod
    def validate_data(cls):
        raise NotImplementedError('class requires a validate_data class method')


class JSONDataPayload(DataPayload):
    def load_data(self):
        data = json.loads(self.src.read_text())
        return data

    def write_to_disk(self, dst: Path = None):
        # self.validate_data()
        if not dst:
            dst = self.src
        print(f'writing to {dst}')
        with open(dst, 'w') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            schema_data = json.load(f)
        jsonschema.validate(self.data, schema_data)
