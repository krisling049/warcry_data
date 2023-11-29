"""
Utility functions and script for data manipulation and management
"""
import json

from data_parsing.fighters import Fighter, FighterJSONDataPayload
from data_parsing.abilities import Ability, AbilityJSONDataPayload
from data_parsing.models import DataPayload, DIST
from data_parsing.warbands import WarbandsJSONDataPayload
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
        faction_match = [x for x in fighters if x.warband == a.warband or a.warband == 'universal']
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


def by_points(fighter: Fighter) -> int:
    return fighter.points


if __name__ == '__main__':
    # fighters = FighterJSONDataPayload()
    # abilities = AbilityJSONDataPayload()

    warbands = WarbandsJSONDataPayload()




    # Do stuff with data, add it to new_data

    # export_files([fighter_data_payload, ability_data_payload])

