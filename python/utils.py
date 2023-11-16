"""
Utility functions and script for data manipulation and management
"""
import json

from data_parsing.fighters import Fighter, FighterJSONDataPayload
from data_parsing.abilities import Ability, AbilityJSONDataPayload
from data_parsing.models import DataPayload, PROJECT_ROOT
from data_parsing.warbands import WarbandDataPayload
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

    fighter_data_payload = FighterJSONDataPayload(
        src_file=Path(PROJECT_ROOT, 'data', 'fighters.json'),
        schema=Path(PROJECT_ROOT, 'data', 'schemas', 'aggregate_fighter_schema.json')
    )
    #
    ability_data_payload = AbilityJSONDataPayload(
        src_file=Path(PROJECT_ROOT, 'data', 'abilities.json'),
        schema=Path(PROJECT_ROOT, 'data', 'schemas', 'aggregate_ability_schema.json')
    )

    blacktalons = WarbandDataPayload(
        warband_file=Path(r'C:\Users\ceckersley\git_personal\warcry_data\data\Order\the_blacktalons.json')
    )

    warbands = dict()
    for fighter in fighter_data_payload.data:
        if fighter['warband'] not in warbands.keys():
            warbands[fighter['warband']] = dict()
        warbands[fighter['warband']]['name'] = fighter['warband']
        warbands[fighter['warband']]['grand_alliance'] = fighter['grand_alliance']
        warbands[fighter['warband']]['_id'] = generate_id()
        warbands[fighter['warband']]['warband_runemark'] = fighter['warband']
        if 'fighters' not in warbands[fighter['warband']].keys():
            warbands[fighter['warband']]['fighters'] = list()
        warbands[fighter['warband']]['fighters'].append(fighter)

    # blacktalons.write_to_disk()

    data_tmp = Path(r'C:\Users\ceckersley\git_personal\warcry_data\data_tmp')
    for v in warbands.values():
        filename = v['name'].lower().replace(' ', '_')
        for illegal_char in r'\\/:*?\"<>|':
            filename = str(filename).replace(illegal_char, '')
        out_path = Path(data_tmp, v['grand_alliance'], f'{filename}.json')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w') as f:
            json.dump(v, f, sort_keys=True, indent=4)


    # warbuubble = [WarbandDataPayload.from_dict(x) for x in warbands.values()]

    x = 1



    # Do stuff with data, add it to new_data

    # export_files([fighter_data_payload, ability_data_payload])

