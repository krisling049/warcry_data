from pathlib import Path
from typing import List, Dict
import json
import jsonschema


PROJECT_ROOT = Path(__file__).parent.parent.parent

class DataPayload:
    """
    The template for handling data. Can be subclassed for other data types (xlsx) in future. Currently intended to
    load data from a single data file (e.g. data/fighters.json).
    """

    def __init__(self, src_file: Path, schema: Path, src_format: str = None):
        self.src_file = src_file
        self.src_format = src_format if src_format else src_file.suffix  # xlsx, json, csv etc
        self.schema = schema
        self.data = self.load_data()
        self.validate_data()

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
        data = json.loads(self.src_file.read_text())
        return data

    def write_to_disk(self, dst: Path = None):
        self.validate_data()
        if not dst:
            dst = self.src_file
        print(f'writing to {dst}')
        with open(dst, 'w') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            schema_data = json.load(f)
        jsonschema.validate(self.data, schema_data)

