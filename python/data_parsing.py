from pathlib import Path
import json
from typing import List, Dict, Tuple
from itertools import product, combinations_with_replacement
import jsonschema
import pandas as pd
import datetime


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

    def __init__(self, src_file: Path, schema: Path, src_format: str = None):
        self.src_file = src_file
        self.src_format = src_format if src_format else src_file.suffix  # xlsx, json, csv etc
        self.schema = schema
        self.data = self.load_data()
        self.validate_data()

    @classmethod
    def load_data(cls):
        raise NotImplementedError('class requires a load_data class method')

    @classmethod
    def write_to_disk(cls):
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

    def write_aggregate_to_disk(self, dst: Path = Path(Path(__file__).parent.parent, 'data', 'fighters.json')):
        self.validate_data()
        sorted_data = [dict(sorted(x.items())) for x in self.data]
        with open(dst, 'w') as nf:
            print(f'Writing {len(self.data)} fighters to {dst}...')
            json.dump(sort_data(sorted_data), nf, ensure_ascii=False, indent=4, sort_keys=False)

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
                    json.dump(sorted_warband, f, ensure_ascii=False, indent=4, sort_keys=False)

    def write_spreadsheet(self, dst_root: Path = Path(Path(__file__).parent.parent, 'data')):
        # This is crap atm. Need to make sure sheet is sensibly ordered and weapons values go into separate columns
        # Also need to add derived statistics (pts/wound, chance to kill vs. T3, T4 etc)
        temp_data = self.data.copy()
        for fighter in temp_data:
            for i, w in enumerate(fighter['weapons']):
                for k, v in w.items():
                    fighter[f'weapon_{i + 1}_{k}'] = v
            del fighter['weapons']

        xlsx_data = pd.DataFrame(temp_data)
        xlsx_data.to_excel(Path(dst_root, 'fighters.xlsx'))

    def write_to_disk(self):
        self.write_aggregate_to_disk()
        self.write_warbands_to_disk()
        self.write_spreadsheet()


class Fighter:
    def __init__(self, fighter_dict: dict):
        for key, value in fighter_dict.items():
            self.__setattr__(key, value)

    def __repr__(self):
        return self.name

    def calc_ctk(
            self,
            vs_t: int,
            vs_w: int,
            weapon_index: int = 0,
            to_crit: int = 6,
            attack_actions: int = 1
    ) -> List[Tuple[int, float]]:
        """
        Calculates the % chance of a weapon killing a fighter with the supplied wounds/toughness.
        :param vs_t: Toughness of the target fighter
        :param vs_w: Wounds of the target fighter
        :param weapon_index: index of the weapon to use, if not provided then the highest ctk will be returned
        :param to_crit: If critting on a roll other than 6, provide the number here
        :param attack_actions: How many actions the fighter can use against the target
        :return: Returns a tuple of the weapon index and that weapon's ctk
        """

        to_check = self.weapons[weapon_index] if weapon_index else self.weapons
        to_ret = list()

        for wep in to_check:
            s = wep['strength']
            a = wep['attacks'] * attack_actions
            dh = wep['dmg_hit']
            dc = wep['dmg_crit']

            to_hit = 4 if s == vs_t else 3 if s > vs_t else 5
            total_rolls = 0
            killing_rolls = 0

            for pr in combinations_with_replacement(range(1, 7), a):
                total_rolls = total_rolls + 1
                damage = 0
                for dice in pr:
                    if dice in range(to_hit, to_crit):
                        damage = damage + dh
                    if dice >= to_crit:
                        damage = damage + dc
                if damage >= vs_w:
                    killing_rolls = killing_rolls + 1
            ctk = killing_rolls / total_rolls
            to_ret.append((weapon_index, ctk))
            if weapon_index == 0:
                weapon_index = weapon_index + 1

        return to_ret

    def has_str(self, s: int) -> bool:
        for wep in self.weapons:
            if wep['strength'] >= s:
                return True
        return False


class AbilityDataPayload(DataPayload):

    def load_data(self):
        raise NotImplementedError('class requires a load_data class method')

    def write_to_disk(self):
        raise NotImplementedError('class requires a write_to_disk class method')

    def validate_data(self):
        raise NotImplementedError('class requires a validate_data class method')


class AbilityJSONPayload(AbilityDataPayload):

    def load_data(self) -> List[Dict]:
        # We treat the abilities.json file as our source of truth so this is the one we load
        with open(self.src_file, 'r') as f:
            data = json.load(f)

        return data

    def write_to_disk(self, dst: Path = Path(Path(__file__).parent.parent, 'data', 'abilities.json')):
        self.validate_data()

        the_data = self.data
        the_data.sort(key=lambda d: d['warband'])

        sorted_data = sorted(the_data, key=lambda d: d['warband'])
        with open(dst, 'w') as nf:
            print(f'Writing {len(self.data)} abilities to {dst}...')
            json.dump(sorted_data, nf, ensure_ascii=False, indent=4, sort_keys=False)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            ability_schema = json.load(f)
        jsonschema.validate(self.data, ability_schema)


class Ability:
    def __init__(self, ability_dict: dict):
        for key, value in ability_dict.items():
            self.__setattr__(key, value)

    def __repr__(self):
        return self.name
