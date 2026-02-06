"""
Fighter utility functions for sorting and analysis.
"""

from typing import List, Tuple, Dict

import pandas as pd

from .config import SchemaFiles
from .models import Fighter

FIGHTER_SCHEMA = SchemaFiles.FIGHTER
FIGHTERS_SCHEMA = SchemaFiles.FIGHTERS_AGGREGATE


def sort_fighters(data_to_sort: List[Dict]) -> List[Dict]:
    for f in data_to_sort:
        f['weapons'] = sorted(f['weapons'], key=lambda x: x['max_range'])
    sorted_data = sorted(
        data_to_sort,
        key=lambda x: (
            x['grand_alliance'],
            x['warband'],
            x['points']
        )
    )

    return sorted_data


def get_extreme_values(fighters: List[Fighter]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Calculate min and max values for all numeric fields across fighters."""
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

    for fighter in fighters:
        for k, v in fighter.as_dict().items():
            if isinstance(v, int):
                update_values(k, v)
            if isinstance(v, list) and all([isinstance(x, dict) for x in v]):
                for d in v:
                    for k2, v2 in d.items():
                        if isinstance(v2, int):
                            update_values(k2, v2)

    return max_values, min_values


def calculate_expected_damages(
        fighters: List[Fighter],
        vs_toughnesses: List[int] = None,
        wounds: List[int] = None
) -> pd.DataFrame:
    """Calculate expected damage probabilities for fighters."""
    if vs_toughnesses is None:
        vs_toughnesses = list(range(3, 8))
    if wounds is None:
        wounds = [3, 4, 6, 8, 10, 12, 15, 20, 25]

    damage_index = list()
    expected_damages = dict()

    for t in vs_toughnesses:
        for w in wounds:
            key = f'T{t}W{w}'
            damage_index.append(key)
            for f in fighters:
                fighter_key = f'{f.name} - {f.warband}'
                if fighter_key not in expected_damages.keys():
                    expected_damages[fighter_key] = list()
                ctk: List[Tuple[Tuple[int, str], float]] = f.dmg_chance(vs_t=t, dmg=w)
                ctk_percent = int(ctk[0][1] * 100)
                expected_damages[fighter_key].append(ctk_percent)

    df = pd.DataFrame(expected_damages, index=damage_index)
    return df


def filter_allies(fighters: List[Fighter]) -> List[Fighter]:
    """Filter fighters that can be used as allies."""
    return [x for x in fighters if 'hero' in x.runemarks or 'ally' in x.runemarks]
