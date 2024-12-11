import json
import re
import uuid
from copy import deepcopy
from pathlib import Path
from typing import List, Dict

import jsonschema

from .abilities import Ability
from .factions import Factions
from .fighters import sort_fighters, Fighter, Fighters, FighterJSONDataPayload
from .models import DataPayload, PROJECT_DATA, PROJECT_ROOT, sanitise_filename, write_data_json


class WarbandsJSONDataPayload(DataPayload):
    def __init__(
            self,
            src: Path = PROJECT_DATA,
            schema: Path = Path(PROJECT_ROOT, 'schemas', 'warband_schema.json'),
            src_format: str = 'json',
            filter_string: str = '*.json'
    ):
        if not src.is_dir():
            raise TypeError(f'src must be a dir: {src}')
        self._filter_str = filter_string
        super().__init__(src, schema, src_format)
        self.fighters = Fighters(self.data['fighters'])
        self.abilities = [Ability(x) for x in self.data['abilities']]
        self.factions = Factions(self.data['factions'])     # type: Factions
        self.assign_factions()
        self.assign_abilities()

    def __repr__(self):
        return 'WarbandData'

    def load_data(self):
        data = {'fighters': list(), 'abilities': list(), 'factions': list()}
        for file in self.src.rglob(self._filter_str):
            if not file.is_file():
                continue
            if file.parent.name.lower() == 'schemas':
                continue
            if file.name.endswith('_fighters.json'):
                data['fighters'].extend(json.loads(file.read_text(encoding='latin-1')))
                continue
            if file.name.endswith('_abilities.json'):
                data['abilities'].extend(json.loads(file.read_text(encoding='latin-1')))
                continue
            if file.name.endswith('_faction.json'):
                data['factions'].append(json.loads(file.read_text(encoding='latin-1')))
                continue
        return data

    def assign_ids(self):
        placeholder_pattern = re.compile(f'^PLACEHOLDER.*|^XXXXXX.*', flags=re.IGNORECASE)

        for data in self.data.values():                 # type: List
            for entity in data:                          # type: Dict
                if '_id' not in entity.keys() or placeholder_pattern.match(entity['_id']):
                    new_id = str(uuid.uuid4()).split('-')[0]
                    print(f'assigning _id for {entity["name"]} - {new_id}')
                    entity['_id'] = new_id

    def assign_abilities(self):

        for a in self.abilities:
            faction_match = [
                x for x in self.fighters.fighters if a.warband in [x.warband, x.subfaction_runemark(), 'universal']
            ]
            for f in faction_match:
                if set(a.runemarks).issubset(set(f.runemarks)):
                    f.abilities.append(a)

    def assign_factions(self):
        for f in self.fighters.fighters:
            for faction in self.factions.factions:
                if f.warband == faction.warband:
                    f.faction = faction
                    for subfaction in faction.subfactions:
                        runemarks_to_check = [*f.runemarks, f.as_dict().get('subfaction')]
                        if any([x for x in [r for r in runemarks_to_check if r] if x == subfaction.runemark]):
                            f.subfaction = subfaction

    def write_fighters_to_disk(self, dst: Path = Path(PROJECT_DATA, 'fighters.json')):
        # self.validate_data()
        sorted_data = sort_fighters([dict(sorted(x.items())) for x in self.data['fighters']])
        write_data_json(dst=dst, data=sorted_data)

    def _exclude_from_tts(self, fighter: Fighter):
        excluded = False
        if fighter.warband == 'Cities of Sigmar':
            excluded = True
        return excluded

    def as_tts_format(self) -> List[dict]:
        tts_data = list()
        for f in self.fighters.fighters:
            if not self._exclude_from_tts(f):
                tts_data.append(f.as_dict())
                tts_abs = [a.tts_format() for a in f.abilities if a.warband != 'universal' and a.cost != 'battletrait']
                tts_data[-1]['abilities'] = tts_abs
        return tts_data

    def write_legacy_fighters(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_legacy_format(dst_root=dst_root)

    def write_tts_fighters(self, dst: Path = Path(PROJECT_DATA, 'tts_fighters.json')):
        write_data_json(dst=dst, data=self.as_tts_format())

    def write_fighters_markdown_table(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_markdown_table(dst_root=dst_root)

    def write_fighters_html(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_html(dst_root=dst_root)

    def write_fighters_xlsx(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_xlsx(dst_root=dst_root)

    def write_fighters_csv(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_csv(dst_root=dst_root)

    def write_abilities_to_disk(self, dst: Path = Path(PROJECT_DATA, 'abilities.json'), exclude_battletraits: bool = False):
        # self.validate_data()
        data = deepcopy(self.data['abilities'])
        if exclude_battletraits:
            data = [x for x in self.data['abilities'] if x['cost'] != 'battletrait']
        sorted_data = sorted(data, key=lambda d: d['warband'])
        write_data_json(dst=dst, data=sorted_data)

    def write_battletraits_to_disk(self, dst: Path = Path(PROJECT_DATA, 'abilities.json')):
        # self.validate_data()
        battletraits = [x for x in self.data['abilities'] if x['cost'] == 'battletrait']
        sorted_data = sorted(battletraits, key=lambda d: d['warband'])
        write_data_json(dst=dst, data=sorted_data)

    def write_warbands_to_disk(self, dst: Path = PROJECT_DATA):
        # self.validate_data()

        data_structure = {'universal': {'faction': {}, 'fighters': list(), 'abilities': list()}}
        faction_mapping = {'universal': 'universal'}    # type: dict[str, str]

        for faction in self.data['factions']:
            if faction['warband'] not in data_structure.keys():
                data_structure[faction['warband']] = {'faction': faction, 'fighters': list(), 'abilities': list()}
            faction_mapping[faction['warband']] = faction['warband']
            for s in faction['subfactions']:
                if s['bladeborn']:
                    faction_mapping[s['runemark']] = faction['warband']

        for fighter in self.data['fighters']:
            data_structure[fighter['warband']]['fighters'].append(fighter)

        for ability in self.data['abilities']:
            faction = faction_mapping[ability['warband']]
            data_structure[faction]['abilities'].append(ability)

        for warband, warband_data in data_structure.items():
            for datatype, content in warband_data.items():
                grand_alliance = 'universal' if warband == 'universal' else warband_data['faction']['grand_alliance']
                faction_runemark = 'universal' if warband == 'universal' else warband_data['faction']['warband']

                if faction_runemark == 'universal' and datatype != 'abilities':
                    continue

                filename = f'{faction_runemark}_{datatype}.json'
                path_parts = [
                    p for p in [
                        dst,
                        grand_alliance,
                        sanitise_filename(faction_runemark) if warband != 'universal' else '',
                        sanitise_filename(filename)
                    ] if p
                ]
                outfile = Path(*path_parts)

                if isinstance(content, list):
                    print(f'{warband} - writing {len(content)} items to {outfile}')
                else:
                    print(f'{warband} - writing {outfile}')

                write_data_json(dst=outfile, data=content)


    def write_to_disk(self, dst_root: Path = PROJECT_DATA):
        self.write_fighters_to_disk(Path(dst_root, 'fighters.json'))
        self.write_abilities_to_disk(Path(dst_root, 'abilities.json'))
        self.write_warbands_to_disk(dst_root)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            warband_schema = json.load(f)
        jsonschema.validate(self.data, warband_schema)

    def write_localised_data(self, loc_file: Path, dst: Path):
        data = sorted(self.get_localisation(patch_file=loc_file), key=lambda d: d['warband'])
        write_data_json(dst=dst, data=data)


    def get_localisation(self, patch_file: Path, encoding: str = 'latin-1') -> List[dict]:
        temp_data = deepcopy(self.data['abilities'])
        loc_data = json.loads(patch_file.read_text(encoding=encoding))     # type: dict
        for ability in temp_data:
            if ability['_id'] in loc_data.keys():
                ability.update(loc_data[ability['_id']])
            else:
                print(f'warning -- {ability["_id"]} - {ability["name"]} - not found in {patch_file}')
        return temp_data

