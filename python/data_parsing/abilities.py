import json
from pathlib import Path
from typing import List, Dict, Optional, Union

import jsonschema

from .models import PROJECT_ROOT, write_data_json

ABILITY_SCHEMA = PROJECT_ROOT / 'schemas' / 'ability_schema.json'
ABILITIES_SCHEMA = PROJECT_ROOT / 'schemas' / 'aggregate_ability_schema.json'


class Ability:
    def __init__(self, ability_dict: dict):
        self._id: str = ability_dict['_id']
        self.name: str = ability_dict['name']
        self.warband: str = ability_dict['warband']
        self.cost: str = ability_dict['cost']
        self.description: str = ability_dict['description']
        self.runemarks: List[str] = ability_dict['runemarks']

    def __repr__(self):
        return self.name

    def tts_format(self) -> Dict[str, str]:
        # tts = {self.name: {'cost': self.cost.capitalize(), 'description': self.description}}
        tts = {'_id': self._id}
        return tts


def load_abilityfile(file: Path) -> List[Ability]:
    from .models import load_json_file
    content = load_json_file(file)
    abilities: List[Ability] = []
    for a in content:
        abilities.append(Ability(ability_dict=a))
    return abilities


class Abilities:
    def __init__(self, abilities: List[Union[Ability, dict]]):
        self.abilities: List[Ability] = []
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
