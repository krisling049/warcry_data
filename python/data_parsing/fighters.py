from itertools import combinations_with_replacement
from pathlib import Path
from typing import List, Tuple, Dict
from .abilities import Ability
from .models import JSONDataPayload, PROJECT_ROOT
import json
import jsonschema
import pandas as pd
from copy import deepcopy


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
        self._raw_data = w_dict                                                                 # type: Dict
        self.attacks = w_dict['attacks']                                                        # type: int
        self.dmg_crit = w_dict['dmg_crit']                                                      # type: int
        self.dmg_hit = w_dict['dmg_hit']                                                        # type: int
        self.max_range = w_dict['max_range']                                                    # type: int
        self.min_range = w_dict['min_range']                                                    # type: int
        self.runemark = w_dict['runemark']                                                      # type: str
        self.strength = w_dict['strength']                                                      # type: int
        self._dmg_rolls = self.damage_rolls()                                                    # type: List[Tuple[int, ...]]
        self.avg_dmg_vs_lower, self.avg_dmg_vs_same, self.avg_dmg_vs_higher = self.avg_dmgs()   # type: float

    def __repr__(self):
        return f'{self.runemark.capitalize()}  -  {self.attacks}/{self.strength}/{self.dmg_hit}/{self.dmg_crit}'

    def as_dict(self):
        return self._raw_data

    def damage_rolls(self) -> List[Tuple[int, ...]]:
        rolls = [x for x in combinations_with_replacement(range(1, 7), self.attacks)]
        return rolls

    def avg_dmgs(self) -> float:
        for i in [3, 4, 5]:
            to_hit = i
            total_rolls = 0
            damages = list()

            for pr in self._dmg_rolls:
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

    def chance_to_kill(
            self,
            target_toughness: int,
            target_wounds: int,
            to_crit: int = 6,
            attack_actions: int = 1
    ) -> float:
        """
        Calculates the % chance of a weapon dealing the given amount of damage to a fighter with the supplied toughness.
        :param target_toughness: Toughness of the target fighter
        :param target_wounds: Target's wounds characteristic
        :param to_crit: If critting on a roll other than 6, provide the number here
        :param attack_actions: How many actions the fighter can use against the target
        :return: a float, % chance to deal target damage)
        """

        to_hit = 4 if self.strength == target_toughness else 3 if self.strength > target_toughness else 5
        total_rolls = 0
        rolls_over_target_dmg = 0

        for pr in combinations_with_replacement(range(1, 7), self.attacks * attack_actions):
            total_rolls += 1
            wounds_caused = 0
            for dice in pr:
                if dice in range(to_hit, to_crit):
                    wounds_caused += self.dmg_hit
                if dice >= to_crit:
                    wounds_caused += self.dmg_crit
            if wounds_caused >= target_wounds:
                rolls_over_target_dmg += 1
        dmg_chance = round(rolls_over_target_dmg / total_rolls, 3)
        return dmg_chance


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
        self._raw_data = profile                                    # type: dict
        self.abilities = list()                                     # type: List[Ability]

    def __repr__(self):
        return self.name

    def as_dict(self) -> dict:
        temp = deepcopy(self._raw_data)
        if self.abilities and all([isinstance(x, str) for x in self.abilities]):
            # this indicates tts-format abilities
            temp['abilities'] = self.abilities
        return temp

    def is_ally(self, src_fighter = None):
        can_ally = any(['hero' in self.runemarks, 'ally' in self.runemarks])
        if src_fighter:
            return all([can_ally, src_fighter.grand_alliance == self.grand_alliance])
        return can_ally


    def dmg_chance(
            self,
            vs_t: int,
            dmg: int,
            weapon_index: int = 0,
            to_crit: int = 6,
            attack_actions: int = 1
    ) -> List[Tuple[Tuple[int, str], float]]:
        """
        Calculates the % chance of a weapon dealing the given amount of damage to a fighter with the supplied toughness.
        :param vs_t: Toughness of the target fighter
        :param dmg: Target damage
        :param weapon_index: index of the weapon to use, if not provided then the highest ctk will be returned
        :param to_crit: If critting on a roll other than 6, provide the number here
        :param attack_actions: How many actions the fighter can use against the target
        :return: Returns a list of ((weapon index, weapon runemark), % chance to deal target damage)
        """

        to_check = self.weapons[weapon_index] if weapon_index else self.weapons
        to_ret = list()

        for wep in to_check:
            chance = wep.chance_to_kill(target_toughness=vs_t, target_wounds=dmg, to_crit=to_crit, attack_actions=attack_actions)
            to_ret.append(((weapon_index, wep.runemark), chance))
            if weapon_index == 0:
                weapon_index += 1

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

    def expected_damages(
            self,
            vs_toughnesses: List[int] = range(3, 8),
            wounds: List[int] = None
    ) -> pd.DataFrame:
        damage_index = list()
        expected_damages = dict()
        if not wounds:
            wounds = [3, 4, 6, 8, 10, 12, 15, 20, 25]
        for t in vs_toughnesses:
            for w in wounds:
                key = f'T{t}W{w}'
                damage_index.append(key)
                for f in self.fighters:
                    fighter_key = f'{f.name} - {f.warband}'
                    if fighter_key not in expected_damages.keys():
                        expected_damages[fighter_key] = list()
                    ctk = f.dmg_chance(vs_t=t, dmg=w)                # type: List[Tuple[Tuple[int, str], float]]
                    ctk_percent = int(ctk[0][1] * 100)
                    expected_damages[fighter_key].append(ctk_percent)
        # ValueError: Length of values (20) does not match length of index (10)
        problem = [{x: expected_damages[x]} for x in expected_damages.keys() if len(expected_damages[x]) != 10]
        df = pd.DataFrame(expected_damages, index=damage_index)
        return df

    def allies(self) -> List[Fighter]:
        allies = [x for x in self.fighters if 'hero' in x.runemarks or 'ally' in x.runemarks]
        return allies


class FighterJSONDataPayload(JSONDataPayload):
    def __init__(
            self,
            src_file: Path = Path(PROJECT_ROOT, 'data', 'fighters.json'),
            schema: Path = Path(PROJECT_ROOT, 'data', 'schemas', 'aggregate_fighter_schema.json'),
            preloaded_data: List[Dict] = None
    ):
        self._preloaded_data = preloaded_data
        super().__init__(src_file, schema, 'json')
        self.fighters = Fighters(self.data)

    def __repr__(self):
        return 'FighterData'

    def load_data(self) -> List[Dict]:
        if self._preloaded_data:
            data = self._preloaded_data
            del self._preloaded_data
            return data
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

    def as_dataframe(self, add_formulae: bool = False) -> pd.DataFrame:
        temp_data = deepcopy(self.data)
        for fighter in temp_data:
            # The fighters need to be flattened for their weapon values to fit into rows/columns
            for i, w in enumerate(fighter['weapons']):
                for k, v in w.items():
                    fighter[f'weapon_{i + 1}_{k}'] = v
            del fighter['weapons']

        return pd.DataFrame(temp_data)

    def write_xlsx(self, dst_root: Path = Path(PROJECT_ROOT, 'data')):
        out_file = Path(dst_root, 'fighters.xlsx')
        to_write = self.as_dataframe()
        print(f'writing {out_file.absolute()}')
        to_write.to_excel(out_file, engine='xlsxwriter')

    def write_markdown_table(self, dst_root: Path = Path(PROJECT_ROOT, 'data')):
        out_file = Path(dst_root, 'fighters.md')
        to_write = self.as_dataframe()
        print(f'writing {out_file.absolute()}')
        to_write.to_markdown(out_file)

    def write_html(self, dst_root: Path = Path(PROJECT_ROOT, 'data')):
        out_file = Path(dst_root, 'fighters.html')
        to_write = self.as_dataframe()
        print(f'writing {out_file.absolute()}')
        to_write.to_html(out_file)

    def write_csv(self, dst_root: Path = Path(PROJECT_ROOT, 'data')):
        out_file = Path(dst_root, 'fighters.csv')
        to_write = self.as_dataframe()
        print(f'writing {out_file.absolute()}')
        to_write.to_csv(out_file)
