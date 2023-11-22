"""
Utility functions and script for data manipulation and management
"""
import json

from data_parsing.fighters import Fighter, FighterJSONDataPayload
from data_parsing.abilities import Ability, AbilityJSONDataPayload
from data_parsing.models import DataPayload, PROJECT_DATA
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

    # for warband in Path(PROJECT_ROOT, 'data').rglob('*.json'):
    #     if warband.name in ['fighters.json', 'abilities.json']:
    #         continue
    #     if warband.parent.name == 'schemas':
    #         continue
    #     payload = FighterJSONDataPayload(src_file=warband)
    #     dst = warband if '_fighters' in warband.name else warband.with_name(f'{warband.stem}_fighters.json')
    #     payload.write_to_disk(dst=dst)

    # abs_by_warband = {'chaos': dict(), 'death': dict(), 'destruction': dict(), 'order': dict(), 'universal': dict()}
    # # {ga: warband: [abilities]}
    # bladeborn_mapping = {'universal': 'universal'}
    # old_cities = [
    #             'Anvilgard Loyalists',
    #             'The Phoenicium',
    #             'Greywater Fastness',
    #             "Tempest's Eye",
    #             'The Living City',
    #             'Hallowheart',
    #             'Hammerhal'
    #         ]
    # for c in old_cities:
    #     bladeborn_mapping[c] = 'Cities of Sigmar'
    #
    # for ability in abilities.data:
    #     grand_alliance = 'universal' if ability['warband'] == 'universal' else None
    #     if not grand_alliance:
    #         if ability['warband'] in old_cities:
    #             grand_alliance = 'order'
    #         for f in fighters.data:
    #             if f['bladeborn']:
    #                 bladeborn_mapping[f['bladeborn']] = f['warband']
    #             bladeborn_mapping[f['warband']] = f['warband']
    #             if f['warband'] == ability['warband'] or f['bladeborn'] == ability['warband']:
    #                 grand_alliance = f['grand_alliance']
    #                 break
    #     if not grand_alliance:
    #         x = 1
    #     if bladeborn_mapping[ability["warband"]] not in abs_by_warband[grand_alliance].keys():
    #         abs_by_warband[grand_alliance][bladeborn_mapping[ability["warband"]]] = list()
    #     abs_by_warband[grand_alliance][bladeborn_mapping[ability["warband"]]].append(ability)
    #
    # for grand_alliance, warbands in abs_by_warband.items():
    #     for warband, warband_abilities in warbands.items():
    #         out_path = Path(PROJECT_ROOT, 'data', grand_alliance, f'{sanitise_filename(warband)}_abilities.json')
    #         sorted_data = sorted(warband_abilities, key=lambda d: d['warband'])
    #         out_path.parent.mkdir(parents=True, exist_ok=True)
    #         with open(out_path, 'w') as f:
    #             print(f'Writing {len(sorted_data)} abilities to {out_path}...')
    #             json.dump(sorted_data, f, ensure_ascii=False, indent=4, sort_keys=False)
    #
    #
    warbands.validate_data()



    # Do stuff with data, add it to new_data

    # export_files([fighter_data_payload, ability_data_payload])

