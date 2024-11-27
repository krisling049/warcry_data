import json
from pathlib import Path
from typing import List, Dict, Optional

import jsonschema

from .models import PROJECT_ROOT, write_data_json

ABILITY_SCHEMA = PROJECT_ROOT / 'schemas' / 'ability_schema.json'
ABILITIES_SCHEMA = PROJECT_ROOT / 'schemas' / 'aggregate_ability_schema.json'


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

    def tts_format(self) -> Dict[str, str]:
        # tts = {self.name: {'cost': self.cost.capitalize(), 'description': self.description}}
        tts = {'_id': self._id}
        return tts


def load_abilityfile(file: Path) -> list[Ability]:
    content = json.loads(file.read_text(encoding='latin-1'))
    abilities = list()
    for a in content:
        abilities.append(Ability(ability_dict=a))
    return abilities


class Abilities:
    def __init__(self, abilities: list[Ability|dict]):
        self.abilities = list()
        for a in abilities:
            if isinstance(a, dict):
                a = Ability(ability_dict=a)
            self.abilities.append(a)

    def __repr__(self):
        return 'AbilityData'

    def write_to_disk(
            self,
            dst: Path = Path(PROJECT_ROOT, 'data', 'abilities.json'),
            schema: Optional[Path] = Path(PROJECT_ROOT, 'data', 'schemas', 'aggregate_ability_schema.json')
    ):
        sorted_data = sorted([x.__dict__ for x in self.abilities], key=lambda d: d['warband'])

        if schema:
            print(f'Validating ability data against {schema}')
            ability_schema = json.loads(schema.read_text())
            jsonschema.validate(sorted_data, ability_schema)

        print(f'Writing {len(sorted_data)} abilities to {dst}...')
        write_data_json(dst=dst, data=sorted_data)
