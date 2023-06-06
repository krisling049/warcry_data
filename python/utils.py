"""
Utility functions and script for data manipulation and management
"""

from data_parsing import FighterJSONPayload, AbilityJSONPayload, Fighter, Ability
from pathlib import Path
from typing import List, Dict


def cheapest_fighters(fighter_data: List[Dict]) -> Dict:
    cheapos = dict()

    grand_alliances = ['chaos', 'death', 'destruction', 'order']
    for ga in grand_alliances:
        cheapos[ga] = min([x for x in fighter_data if x['grand_alliance'] == ga], key=lambda x: x['points'])

    return cheapos


if __name__ == '__main__':
    srcs = [
        Path(Path(__file__).parent.parent, 'data', 'fighters.json'),
        Path(Path(__file__).parent.parent, 'data', 'abilities.json')
    ]

    fighter_data_payload = FighterJSONPayload(
        src_file=srcs[0],
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_fighter_schema.json')
    )
    fighter_data = fighter_data_payload.data

    ability_data_payload = AbilityJSONPayload(
        src_file=srcs[1],
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_ability_schema.json')
    )
    ability_data = ability_data_payload.data

    abilities = [Ability(x) for x in ability_data]
    fighters = [Fighter(x) for x in fighter_data]


    # Do stuff with data, add it to new_data

    # fighter_data_payload.write_aggregate_file_to_disk()
    # fighter_data_payload.write_warbands_to_disk()
    # ability_data_payload.write_to_disk(dst=Path(r'C:\Users\ceckersley\git_personal\warcry_data\data\abilities_test.json'))
    # data_payload.write_spreadsheet()

    z = 1 + 2
