from pathlib import Path
import json


class DataPayload:
    """
    The template for handling data. Can be subclassed for other data types (xlsx) in future. Currently intended to
    load data from a single data file (e.g. data/fighters.json).
    """

    def __init__(self, src_file: Path, src_format: str = None):
        self.src_file = src_file
        self.src_format = src_format if src_format else src_file.suffix  # xlsx, json, csv etc
        self.data = self.load_data()

    @classmethod
    def load_data(cls):
        raise NotImplementedError('class requires a load_data class method')

    @classmethod
    def write_to_disk(cls, dst: Path):
        raise NotImplementedError('class requires a write_to_disk class method')


class JSONPayload(DataPayload):

    def load_data(self):
        if self.src_format.lower().lstrip('.') != 'json':
            raise RuntimeError(f'{self.src_format} is not a json file!')
        with open(self.src_file, 'r') as f:
            data_json = json.load(f)
        return data_json

    def write_to_disk(self, dst: Path):
        with open(dst, 'w') as nf:
            json.dump(self.data, nf, ensure_ascii=True, indent=4, sort_keys=True)

    def write_warbands_to_disk(self, dst_root: Path = Path(Path(__file__).parent.parent, 'data')):
        pass

