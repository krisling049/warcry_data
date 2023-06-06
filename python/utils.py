"""
Utility functions and script for data manipulation and management
"""
import json

from data_parsing import FighterJSONPayload, AbilityJSONPayload, sort_data, Fighter
from pathlib import Path
from typing import List, Dict
import uuid
import xml.etree.ElementTree as ET
import pandas as pd
import os
import re
import encodings


def cheapest_fighters(fighter_data: List[Dict]) -> Dict:
    cheapos = dict()

    grand_alliances = ['chaos', 'death', 'destruction', 'order']
    for ga in grand_alliances:
        cheapos[ga] = min([x for x in fighter_data if x['grand_alliance'] == ga], key=lambda x: x['points'])

    return cheapos


def get_fighter_type(dude: dict) -> dict:
    types = list()
    for t in ['hero', 'monster', 'thrall', 'ally']:
        if t in dude['runemarks']:
            types.append(t)
    if dude['bladeborn']:
        types.append('bladeborn')
    if len(types) == 0:
        types.append('fighter')
    dude['fighter_type'] = types
    return dude


def generate_id(guy: dict) -> dict:
    # This should be how ids are generated. Once a fighter has an id, they should not be given a new one.
    if '_id' in guy.keys():
        return guy

    guy['_id'] = str(uuid.uuid4()).split('-')[0]
    return guy


def read_bsdata(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # z = tree.findall(r'./{http://www.battlescribe.net/schema/catalogueSchema}rules}')
    abilities = list()
    ability_pattern = re.compile(r'^.+\[(.+)] (.+)$')
    for rule in root.findall('.//{*}rules/{*}rule'):
        description = None
        full_name = rule.attrib['name']
        matches = re.match(ability_pattern, full_name)
        cost = matches.group(1)
        name = matches.group(2)
        for desc in rule.findall('.//{*}description'):
            description = desc.text
        if description:
            # {'⚁ [Double] Brayherd Ambush': 'A fighter can use this ability only if it is the first battle round. This fighter can make a bonus move action a number of inches equal to the value of this ability.'}
            abilities.append({str(uuid.uuid4()).split('-')[0]: {'name': name, 'cost': cost, 'text': description, 'faction': xml_file.name.split('-')[1]}})
        else:
            beep = 'boop'

    ability_schema = {'name': str, 'value': str, 'ability_text': str, 'faction': str}
    return abilities


def bs_ability_data():
    ...


def convert_ability(ability: dict, known_warbands: set, known_bladeborn: set) -> dict:

    new_ability = {
        '_id': str(uuid.uuid4()).split('-')[0],
        'name': None,
        'warband': None,
        'cost': None,
        'description': None,
        'runemarks': None
    }

    dice_to_cost = ['reaction', 'one', 'double', 'triple', 'quad']

    for key, value in ability.items():
        if key in new_ability.keys():
            new_ability[key] = value
            if key == 'runemarks':
                bborn = list(set(value).intersection(known_bladeborn))
                if len(bborn) == 1:
                    new_ability['warband'] = bborn[0]
                if not new_ability['warband']:
                    try:
                        new_ability['warband'] = list(set(value).intersection(known_warbands))[0]
                    except IndexError:
                        new_ability['warband'] = ''

                new_ability['runemarks'] = [
                    r.lower() for r in value if r not in list(known_warbands) + list(known_bladeborn)
                ]
        else:
            if key == 'dice':
                new_ability['cost'] = dice_to_cost[value]
        if not new_ability['cost']:
            new_ability['cost'] = dice_to_cost[0]

    return new_ability


def convert_universal_ability(universal_ability: dict) -> dict:
    new_universal_ability = {'name': None, 'warband': None, 'cost': None, 'description': None, 'runemarks': None}
    dice_to_cost = ['reaction', 'one', 'double', 'triple', 'quad']
    for key, value in universal_ability.items():
        if key in new_universal_ability.keys():
            new_universal_ability[key] = value
        else:
            if key == 'dice':
                new_universal_ability['cost'] = dice_to_cost[value]
    new_universal_ability['warband'] = 'universal'
    if not new_universal_ability['cost']:
        new_universal_ability['cost'] = dice_to_cost[0]

    return {str(uuid.uuid4()).split('-')[0]: new_universal_ability}


if __name__ == '__main__':
    src_data = Path(Path(__file__).parent.parent, 'data', 'fighters.json')

    fighter_data_payload = FighterJSONPayload(
        src_file=src_data,
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_fighter_schema.json')
    )
    fighter_data = fighter_data_payload.data

    ability_data_payload = AbilityJSONPayload(
        src_file=src_data,
        schema=Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_ability_schema.json')
    )


    # new_data = list()  # type: List[Dict]

    bladeborns = set()
    factions = set()
    for x in fighter_data:
        factions.add(x['warband'])
        if x['bladeborn']:
            bladeborns.add(x['bladeborn'])

    abilities = list()
    for root, dirs, files in os.walk(
            r'C:\Users\ceckersley\git_personal\warcry_data\data\abilities\abilties-and-reactions'):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                try:
                    beep = json.load(f)
                    if file == 'index.json':
                        for a in beep:
                            abilities.append(convert_universal_ability(a))
                    else:
                        abs = beep['abilities'] + [beep['reaction']] if beep['reaction'] else list()
                        for a in abs:
                            try:
                                abilities.append(
                                    convert_ability(a, known_warbands=factions, known_bladeborn=bladeborns))
                            except Exception as e:
                                print(e)
                except UnicodeDecodeError as e:
                    pass

    with open(r'C:\Users\ceckersley\git_personal\warcry_data\data\abilities.json', 'w') as f:
        json.dump(abilities, f, indent=4, ensure_ascii=False, sort_keys=False)

    # abilities = list()
    # for root, dir, files in os.walk(r'C:\Users\ceckersley\git_personal\warhammer-age-of-sigmar-warcry'):
    #     for file in files:
    #         if 'LeadersAbilities' in file:
    #             abilities.extend(read_bsdata(Path(root, file)))
    #
    # with open(r'C:\Users\ceckersley\git_personal\warcry_data\data\abilities.json', 'w') as f:
    #     json.dump(abilities, f, indent=4)

    # Do stuff with data, add it to new_data


    # data_payload.data = sort_data(new_data)

    # fighters = [Fighter(x) for x in data]

    # def sort_pts(guy: Fighter):
    #     return guy.points
    #
    # # cos_toughies = sorted(
    # #     [Fighter(f) for f in data if f['warband'] == 'Cities of Sigmar' and 'hero' in f['runemarks'] and 'mount' in f['runemarks']],
    # #     key=sort_pts
    # # )
    #
    # hitters = sorted([f for f in fighters if f.warband == 'Cities of Sigmar' and f.has_str(5)], key=sort_pts)

    # for f in fighters:
    #     setattr(f, 'ctk_t3w8_actn2', f.ctk(t=3, w=8, attack_actions=2))
    #     setattr(f, 'ctk_t4w10_actn2', f.ctk(t=4, w=10, attack_actions=2))

    # best_vs_t4w10 = sorted([x for x in fighters if x.ctk_t4w10 >= 0.75], key=lambda x: x.points)


    # t3killers = sorted([x for x in fighters if x.ctk(t=3, w=8) > 0.75], key=lambda x: x.points)
    # non_hero_t3killers = sorted([x for x in fighters if 'hero' not in x.runemarks and x.ctk(t=3, w=8) > 0.75], key=lambda x: x.points)
    # t3killers = sorted([x for x in fighters if x.ctk(t=3, w=8) > 0.75], key=lambda x: x.points)
    # non_hero_t3killers = sorted([x for x in fighters if 'hero' not in x.runemarks and x.ctk(t=3, w=8) > 0.75],
                                # key=lambda x: x.points)
    # t4killers = sorted([x for x in fighters if x.ctk(t=4, w=10) > 0.8], key=sort_pts)

    # data_payload.write_aggregate_file_to_disk()
    # data_payload.write_warbands_to_disk()

    # data_payload.write_spreadsheet()

    z = 1 + 2
