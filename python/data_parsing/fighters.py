from itertools import combinations_with_replacement
from pathlib import Path
from typing import List, Tuple, Dict
from .abilities import Ability
from .models import JSONDataPayload, PROJECT_ROOT
import json
import jsonschema
import pandas as pd


def sort_fighters(data_to_sort: List[Dict]) -> List[Dict]:
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


class Weapon:
    def __init__(self, w_dict: dict):
        self.attacks = w_dict['attacks']                                                        # type: int
        self.dmg_crit = w_dict['dmg_crit']                                                      # type: int
        self.dmg_hit = w_dict['dmg_hit']                                                        # type: int
        self.max_range = w_dict['max_range']                                                    # type: int
        self.min_range = w_dict['min_range']                                                    # type: int
        self.runemark = w_dict['runemark']                                                      # type: str
        self.strength = w_dict['strength']                                                      # type: int
        self.dmg_rolls = self.damage_rolls()                                                    # type: List[Tuple[int]]
        self.avg_dmg_vs_lower, self.avg_dmg_vs_same, self.avg_dmg_vs_higher = self.avg_dmgs()   # type: float

    def __repr__(self):
        return self.runemark

    def damage_rolls(self) -> List[Tuple[int]]:
        rolls = [x for x in combinations_with_replacement(range(1, 7), self.attacks)]
        return rolls

    def avg_dmgs(self) -> float:
        for i in [3, 4, 5]:
            to_hit = i
            total_rolls = 0
            damages = list()

            for pr in self.dmg_rolls:
                total_rolls = total_rolls + 1
                damage = 0
                for dice in pr:
                    if dice in range(to_hit, 6):
                        damage = damage + self.dmg_hit
                    if dice >= 6:
                        damage = damage + self.dmg_crit
                damages.append(damage)

            avg = sum(damages) / len(damages)
            yield avg


class Fighter:
    def __init__(self, profile: dict):
        self._id = profile['_id']                                   # type: str
        self.bladeborn = profile['bladeborn']                       # type: str
        self.grand_alliance = profile['grand_alliance']             # type: str
        self.movement = profile['movement']                         # type: int
        self.name = profile['name']                                 # type: str
        self.points = profile['points']                             # type: int
        self.runemarks = profile['runemarks']                       # type: List[str]
        self.toughness = profile['toughness']                       # type: int
        self.warband = profile['warband']                           # type: str
        self.weapons = [Weapon(x) for x in profile['weapons']]      # type: List[Weapon]
        self.wounds = profile['wounds']                             # type: int
        self.abilities = list()                                     # type: List[Ability]

    def __repr__(self):
        return self.name

    def as_dict(self) -> dict:
        return self.__dict__

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
            s = wep.strength
            a = wep.attacks * attack_actions
            dh = wep.dmg_hit
            dc = wep.dmg_crit

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
            to_ret.append(((weapon_index, wep.runemark), ctk))
            if weapon_index == 0:
                weapon_index = weapon_index + 1

        return to_ret

    def has_str(self, s: int) -> bool:
        for wep in self.weapons:
            if wep.strength >= s:
                return True
        return False


class Fighters:
    def __init__(self, fighters: List[Dict]):
        self.fighters = [Fighter(x) for x in fighters]
        self.max_values, self.min_values = self._get_extreme_values()

    def _get_extreme_values(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        max_values = dict()
        min_values = dict()

        def update_values(key: str, value: int):
            if key not in max_values.keys():
                max_values[key] = value
            else:
                max_values[key] = value if value > max_values[key] else max_values[key]
            if key not in min_values.keys():
                min_values[key] = value
            else:
                min_values[key] = value if value < min_values[key] else min_values[key]

        for fighter in self.fighters:
            for k, v in fighter.as_dict().items():
                if isinstance(v, int):
                    update_values(k, v)
                if isinstance(v, list) and all([isinstance(x, dict) for x in v]):
                    for d in v:
                        for k2, v2 in d.items():
                            if isinstance(v2, int):
                                update_values(k2, v2)

        return max_values, min_values

    def expected_damages(self) -> pd.DataFrame:
        damage_index = list()
        expected_damages = dict()
        for t in range(3, 8):
            for w in [3, 4, 6, 8, 10, 12, 15, 20, 25]:
                key = f'T{t}W{w}'
                damage_index.append(key)
                for f in self.fighters:
                    if f.name not in expected_damages.keys():
                        expected_damages[f.name] = list()
                    ctk = f.calc_ctk(vs_t=t, vs_w=w)                # type: list[tuple[int, float]]
                    ctk_percent = int(ctk[0][1] * 100)
                    expected_damages[f.name].append(ctk_percent)

        df = pd.DataFrame(expected_damages, index=damage_index)
        return df


class FighterJSONDataPayload(JSONDataPayload):
    def __init__(
            self,
            src_file: Path = Path(PROJECT_ROOT, 'data', 'fighters.json'),
            schema: Path = Path(PROJECT_ROOT, 'data', 'schemas', 'aggregate_fighter_schema.json')
    ):
        super().__init__(src_file, schema, 'json')
        self.fighters = Fighters(self.data)

    def load_data(self) -> List[Dict]:
        # We treat the fighters.json file as our source of truth so this is the one we load
        with open(self.src, 'r') as f:
            data = json.load(f)  # type: List[Dict]
        return data

    def write_to_disk(self, dst: Path = Path(Path(__file__).parent.parent, 'data', 'fighters.json')):
        self.validate_data()
        sorted_data = [dict(sorted(x.items())) for x in self.data]
        with open(dst, 'w') as nf:
            print(f'Writing {len(self.data)} fighters to {dst}...')
            json.dump(sort_fighters(sorted_data), nf, ensure_ascii=False, indent=4, sort_keys=False)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            aggregate_schema = json.load(f)
        jsonschema.validate(self.data, aggregate_schema)

    def as_dataframe(self) -> pd.DataFrame:
        temp_data = self.data.copy()
        # The fighters need to be flattened for their weapon values to fit into rows/columns
        for fighter in temp_data:
            for i, w in enumerate(fighter['weapons']):
                for k, v in w.items():
                    fighter[f'weapon_{i + 1}_{k}'] = v
            del fighter['weapons']

        return pd.DataFrame(temp_data)

    def write_xlsx(self, dst_root: Path = Path(PROJECT_ROOT, 'data_tmp')):
        to_write = self.as_dataframe()
        to_write.to_excel(Path(dst_root, 'fighters.xlsx'))

    def write_markdown_table(self, dst_root: Path = Path(PROJECT_ROOT, 'data_tmp')):
        to_write = self.as_dataframe()
        to_write.to_markdown(Path(dst_root, 'fighters.md'))
