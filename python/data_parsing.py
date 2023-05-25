from pathlib import Path
import json
from typing import List, Dict
from itertools import product
import jsonschema
import pandas as pd


def sort_data(data_to_sort: List[Dict]) -> List[Dict]:
    for f in data_to_sort:
        f['weapons'] = sorted(f['weapons'], key=lambda x: x['max_range'])
    sorted_data = sorted(
        data_to_sort,
        key=lambda x: (
            x['grand_alliance'],
            x['warband'],
            x['bladeborn'],
            x['points']
        )
    )

    return sorted_data


class DataPayload:
    """
    The template for handling data. Can be subclassed for other data types (xlsx) in future. Currently intended to
    load data from a single data file (e.g. data/fighters.json).
    """

    def __init__(self, src_file: Path, src_format: str = None):
        self.src_file = src_file
        self.src_format = src_format if src_format else src_file.suffix  # xlsx, json, csv etc
        self.schema = Path(Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_schema.json')
        self.data = self.load_data()
        self.validate_data()

    @classmethod
    def load_data(cls):
        raise NotImplementedError('class requires a load_data class method')

    @classmethod
    def write_to_disk(cls, dst: Path):
        raise NotImplementedError('class requires a write_to_disk class method')

    @classmethod
    def validate_data(cls):
        raise NotImplementedError('class requires a validate_data class method')


# noinspection PyAbstractClass
class FighterDataPayload(DataPayload):

    @classmethod
    def write_warbands_to_disk(cls, dst_root):
        raise NotImplementedError('class requires a write_warbands_to_disk class method')


class FighterJSONPayload(FighterDataPayload):

    def load_data(self) -> List[Dict]:
        # We treat the fighters.json file as our source of truth so this is the one we load
        with open(self.src_file, 'r') as f:
            data = json.load(f)
        return data

    def write_aggregate_file_to_disk(self, dst: Path = Path(Path(__file__).parent.parent, 'data', 'fighters.json')):
        self.validate_data()
        sorted_data = [dict(sorted(x.items())) for x in self.data]
        with open(dst, 'w') as nf:
            print(f'Writing {len(self.data)} fighters to {dst}...')
            json.dump(sort_data(sorted_data), nf, ensure_ascii=True, indent=4, sort_keys=False)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            aggregate_schema = json.load(f)
        jsonschema.validate(self.data, aggregate_schema)

    def write_warbands_to_disk(self, dst_root: Path = Path(Path(__file__).parent.parent, 'data')):

        self.validate_data()
        warband_by_ga = dict()

        for fighter in self.data:
            fighter = dict(sorted(fighter.items()))
            if fighter['grand_alliance'] not in warband_by_ga.keys():
                warband_by_ga[fighter['grand_alliance']] = dict()
            if fighter['warband'] not in warband_by_ga[fighter['grand_alliance']].keys():
                warband_by_ga[fighter['grand_alliance']][fighter['warband']] = list()
            warband_by_ga[fighter['grand_alliance']][fighter['warband']].append(fighter)

        for GA, WARBANDS in warband_by_ga.items():
            for warband, fighters in WARBANDS.items():
                data_path = Path(dst_root, GA.lower())
                filename = warband.lower().replace(' ', '_') + '.json'
                for illegal_char in r'\\/:*?\"<>|':
                    filename = str(filename).replace(illegal_char, '')
                data_path.mkdir(parents=True, exist_ok=True)
                output_file = Path(data_path, filename)
                with open(output_file, 'w') as f:
                    print(f'Writing {len(WARBANDS[warband])} fighters to {output_file}')
                    sorted_warband = sort_data(WARBANDS[warband])
                    json.dump(sorted_warband, f, ensure_ascii=True, indent=4, sort_keys=False)

    def write_spreadsheet(self, dst_root: Path = Path(Path(__file__).parent.parent, 'data')):
        # This is crap atm. Need to make sure sheet is sensibly ordered and weapons values go into separate columns
        # Also need to add derived statistics (pts/wound, chance to kill vs. T3, T4 etc)
        xlsx_data = pd.DataFrame(self.data)
        xlsx_data.to_excel(Path(dst_root, 'fighters.xlsx'))


class Fighter:
    def __init__(self, fighter_dict: dict):
        self.name = fighter_dict['name']
        self._id = fighter_dict['_id']
        self.bladeborn = fighter_dict['bladeborn']
        self.grand_alliance = fighter_dict['grand_alliance']
        self.movement = fighter_dict['movement']
        self.points = fighter_dict['points']
        self.runemarks = fighter_dict['runemarks']
        self.toughness = fighter_dict['toughness']
        self.warband = fighter_dict['warband']
        self.weapons = fighter_dict['weapons']
        self.wounds = fighter_dict['wounds']

    def __repr__(self):
        return self.name

    def ctk(self, t: int, w: int, to_crit: int = 6) -> float:
        for wep in self.weapons:
            s = wep['strength']
            a = wep['attacks']
            dh = wep['dmg_hit']
            dc = wep['dmg_crit']

            to_hit = 4 if s == t else 3 if s > t else 5
            possible_rolls = list(product(*[list(range(1, 7)) for _ in range(a)]))
            killing_rolls = 0
            for pr in possible_rolls:
                damage = 0
                for dice in pr:
                    if dice in range(to_hit, to_crit):
                        damage = damage + dh
                    if dice >= to_crit:
                        damage = damage + dc
                if damage >= w:
                    killing_rolls = killing_rolls + 1
            ctk = killing_rolls / len(possible_rolls)
            return ctk

    def has_str(self, s: int) -> bool:
        for wep in self.weapons:
            if wep['strength'] >= s:
                return True
        return False

