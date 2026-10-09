from copy import deepcopy

from .abilities import Ability


def sort_fighters(data_to_sort: list[dict]) -> list[dict]:
    for f in data_to_sort:
        f['weapons'] = sorted(f['weapons'], key=lambda x: x['max_range'])
    return sorted(data_to_sort, key=lambda x: (x['grand_alliance'], x['warband'], x['points']))


class Fighter:
    def __init__(self, profile: dict):
        self.name: str = profile['name']
        self.warband: str = profile['warband']
        self.runemarks: list[str] = profile['runemarks']
        self.declared_subfaction: str = profile['subfaction']
        # Empty when the fighter belongs to no subfaction of its warband.
        self.subfaction: str = ''
        self.abilities: list[Ability] = []
        self._raw_data: dict = profile

    def __repr__(self) -> str:
        return self.name

    def as_dict(self) -> dict:
        return deepcopy(self._raw_data)
