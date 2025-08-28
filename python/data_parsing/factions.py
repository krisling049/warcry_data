from pathlib import Path
from typing import Set, List

from .models import PROJECT_ROOT, PROJECT_DATA, sanitise_filename, write_data_json

FACTION_SCHEMA = PROJECT_ROOT / 'schemas' / 'faction_schema.json'


class SubFaction:
    def __init__(self, runemark: str, bladeborn: bool = False, heroes_all: bool = False):
        self.runemark = runemark
        self.bladeborn = bladeborn
        self.heroes_all = heroes_all

    def __repr__(self):
        return self.runemark

class Faction:
    def __init__(self, grand_alliance: str, warband: str, bladeborn: bool = False, heroes_all: bool = False):
        self.grand_alliance = grand_alliance
        self.warband = warband
        self.bladeborn = bladeborn
        self.heroes_all = heroes_all
        self.subfactions: Set[SubFaction] = set()

    def __repr__(self):
        return self.warband

    def as_dict(self):
        json_serialisable = {
            'grand_alliance': self.grand_alliance,
            'warband': self.warband,
            'bladeborn': self.bladeborn,
            'heroes_all': self.heroes_all,
            'subfactions': [s.__dict__ for s in self.subfactions]
        }
        return json_serialisable

    def get_bladeborn(self) -> set[str]:
        return set([b.runemark for b in self.subfactions if b.bladeborn])

    def write_file(self, dst: Path = PROJECT_DATA):
        outfile = dst / self.grand_alliance.title() / sanitise_filename(self.warband) / sanitise_filename(f'{self.warband}.json')
        write_data_json(dst=outfile, data=self.as_dict())


class Factions:
    def __init__(self, data: List[dict]):
        self.factions: List[Faction] = []
        self.bladeborn_runemarks: Set[str] = set()
        for f in data:
            new_faction = Faction(
                    grand_alliance=f['grand_alliance'],
                    warband=f['warband'],
                    bladeborn=f['bladeborn'],
                    heroes_all=f['heroes_all']
                )
            if new_faction.bladeborn:
                self.bladeborn_runemarks.add(new_faction.warband)
            for s in f['subfactions']:
                new_subfaction = SubFaction(
                        runemark=s['runemark'],
                        bladeborn=s['bladeborn'],
                        heroes_all=s['heroes_all']
                    )
                if new_subfaction.bladeborn:
                    self.bladeborn_runemarks.add(new_subfaction.runemark)
                new_faction.subfactions.add(new_subfaction)
            self.factions.append(new_faction)
