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


    # Do stuff with data, add it to new_data

    # fighter_data_payload.write_aggregate_file_to_disk()
    # fighter_data_payload.write_warbands_to_disk()
    # ability_data_payload.write_to_disk(dst=Path(r'C:\Users\ceckersley\git_personal\warcry_data\data\abilities_test.json'))
    # data_payload.write_spreadsheet()

    z = 1 + 2
