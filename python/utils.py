"""
Utility functions and script for data manipulation and management
"""

from data_parsing import FighterJSONPayload, AbilityJSONPayload, Fighter, Ability, DataPayload
from pathlib import Path
from typing import List, Dict
import uuid


def cheapest_fighters(fighter_data: List[Dict]) -> Dict:
    cheapos = dict()

    grand_alliances = ['chaos', 'death', 'destruction', 'order']
    for ga in grand_alliances:
        cheapos[ga] = min([x for x in fighter_data if x['grand_alliance'] == ga], key=lambda x: x['points'])

    return cheapos


def generate_id() -> str:
    return str(uuid.uuid4()).split('-')[0]


def export_files(payloads: List[DataPayload]):
    """
    :param payloads: (DataPayload subclass, path to output folder)
    """
    for p in payloads:
        p.write_to_disk()


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

    export_files([fighter_data_payload, ability_data_payload])

    z = 1 + 2
