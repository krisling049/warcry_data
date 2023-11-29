from typing import List
from pathlib import Path
import json
import jsonschema
from .models import JSONDataPayload, PROJECT_ROOT


class Ability:
    def __init__(self, ability_dict: dict):
        self._id = ability_dict['_id']                      # type: str
        self.name = ability_dict['name']                    # type: str
        self.warband = ability_dict['warband']              # type: str
        self.cost = ability_dict['cost']                    # type: str
        self.description = ability_dict['description']      # type: str
        self.runemarks = ability_dict['runemarks']          # type: List[str]

    def __repr__(self):
        return self.name

    def tts_format(self) -> dict:
        tts = {self.name: {'cost': self.cost.capitalize(), 'description': self.description}}
        return tts


class AbilityJSONDataPayload(JSONDataPayload):
    def __init__(
            self,
            src_file: Path = Path(PROJECT_ROOT, 'data', 'abilities.json'),
            schema: Path = Path(PROJECT_ROOT, 'data', 'schemas', 'aggregate_ability_schema.json')
    ):
        super().__init__(src_file, schema)

    def __repr__(self):
        return 'AbilityData'

    def write_to_disk(self, dst: Path = Path(PROJECT_ROOT, 'data', 'abilities.json')):
        self.validate_data()

        the_data = self.data
        the_data.sort(key=lambda d: d['warband'])

        sorted_data = sorted(the_data, key=lambda d: d['warband'])
        with open(dst, 'w') as nf:
            print(f'Writing {len(self.data)} abilities to {dst}...')
            json.dump(sorted_data, nf, ensure_ascii=False, indent=4, sort_keys=False)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            ability_schema = json.load(f)
        jsonschema.validate(self.data, ability_schema)
