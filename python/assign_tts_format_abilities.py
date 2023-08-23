import json
from data_parsing import FighterJSONPayload, AbilityJSONPayload
from pathlib import Path
from typing import List, Dict


def assign_abilities(fighters: List[Dict], abilities: List[Dict]) -> List[Dict]:

    for a in abilities:
        faction_match = [x for x in fighters if x['warband'] == a['warband'] or x['bladeborn'] == a['warband']]
        for f in faction_match:
            if set(a['runemarks']).issubset(set(f['runemarks'])):
                f['abilities'].append(a)

    return fighters


def convert_ability_format(fighter: Dict):
    new_abilities = list()
    for a in fighter['abilities']:
        if a['warband'] == 'universal':
            continue
        new_abilities.append(f'{a["cost"].capitalize()} - {a["name"]}')
    fighter['abilities'] = sorted(new_abilities)
    return fighter


if __name__ == '__main__':

    fighters = FighterJSONPayload(
        src_file=Path(Path(__file__).parent.parent, 'data', 'fighters.json'),
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_fighter_schema.json')
    ).data

    abilities = AbilityJSONPayload(
        src_file=Path(Path(__file__).parent.parent, 'data', 'abilities.json'),
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_ability_schema.json')
    ).data

    for f in fighters:
        f['abilities'] = list()

    new_fighters = assign_abilities(fighters, abilities)
    for f in new_fighters:
        convert_ability_format(f)

    with open(Path(Path(__file__).parent.parent, 'data', 'tts_fighters.json'), 'w') as f:
        json.dump(new_fighters, f, sort_keys=True, indent=4)
