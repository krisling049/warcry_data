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


def assign_abilities(fighters: List[Fighter], abilities: List[Ability]) -> List[Fighter]:
    for f in fighters:
        f.__setattr__('abilities', list())

    for a in abilities:
        faction_match = [x for x in ftrs if x.warband == a.warband or a.warband == 'universal']
        for f in faction_match:
            if set(a.runemarks).issubset(set(f.runemarks)):
                f.abilities.append(a)

    return fighters

def generate_id() -> str:
    return str(uuid.uuid4()).split('-')[0]


def export_files(payloads: List[DataPayload]):
    """
    :param payloads: (DataPayload subclass, path to output folder)
    """
    for p in payloads:
        p.write_to_disk()


if __name__ == '__main__':

    fighter_data_payload = FighterJSONPayload(
        src_file=Path(Path(__file__).parent.parent, 'data', 'fighters.json'),
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_fighter_schema.json')
    )

    ability_data_payload = AbilityJSONPayload(
        src_file=Path(Path(__file__).parent.parent, 'data', 'abilities.json'),
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_ability_schema.json')
    )

    abs = [Ability(x) for x in abilities.data]
    ftrs = [Fighter(x) for x in fighters.data]
    ftrs = assign_abilities(fighters=ftrs, abilities=abs)

    # Do stuff with data, add it to new_data

    # export_files([fighter_data_payload, ability_data_payload])
    # ability_data_payload.write_to_disk()
    # fighter_data_payload.write_to_disk()

    z = 1 + 2
