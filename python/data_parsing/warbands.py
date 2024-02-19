from .fighters import sort_fighters, Fighter, Fighters, FighterJSONDataPayload
from .abilities import Ability
from .models import DataPayload, PROJECT_DATA, sanitise_filename, DIST
from pathlib import Path
from typing import Union, List, Dict
import json
import jsonschema
import re
import uuid


class WarbandsJSONDataPayload(DataPayload):
    def __init__(
            self,
            src: Path = PROJECT_DATA,
            schema: Path = Path(PROJECT_DATA, 'schemas', 'warband_schema.json'),
            src_format: str = 'json',
            filter_string: str = '*_*.json'
    ):
        if not src.is_dir():
            raise TypeError(f'src must be a dir: {src}')
        self._filter_str = filter_string
        super().__init__(src, schema, src_format)
        self.fighters = Fighters(self.data['fighters'])
        self.abilities = [Ability(x) for x in self.data['abilities']]
        self.assign_abilities()

    def __repr__(self):
        return 'WarbandData'

    def load_data(self):
        data = {'fighters': list(), 'abilities': list()}
        for file in self.src.rglob(self._filter_str):
            if not file.is_file():
                continue
            if file.parent.name.lower() == 'schemas':
                continue
            if file.name.endswith('_fighters.json'):
                data['fighters'].extend(json.loads(file.read_text()))
                continue
            if file.name.endswith('_abilities.json'):
                data['abilities'].extend(json.loads(file.read_text()))
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
            faction_match = [x for x in self.fighters.fighters if x.warband == a.warband or a.warband == 'universal']
            for f in faction_match:
                if set(a.runemarks).issubset(set(f.runemarks)):
                    f.abilities.append(a)

    def _write_json(self, dst: Path, data: Union[List, Dict]):
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, 'w') as f:
            print(f'writing {len(data)} items to {dst}')
            json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=False)

    def write_fighters_to_disk(self, dst: Path = Path(PROJECT_DATA, 'fighters.json')):
        self.validate_data()
        sorted_data = sort_fighters([dict(sorted(x.items())) for x in self.data['fighters']])
        self._write_json(dst=dst, data=sorted_data)

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
                ab_dict = dict()
                for ability in [a for a in f.abilities if a.warband != 'universal']:
                    ab_dict.update(ability.tts_format())
                tts_data[-1]['abilities'] = ab_dict
        return tts_data

    def write_tts_fighters(self, dst: Path = Path(PROJECT_DATA, 'tts_fighters.json')):
        self._write_json(dst=dst, data=self.as_tts_format())

    def write_fighters_markdown_table(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_markdown_table(dst_root=dst_root)

    def write_fighters_html(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_html(dst_root=dst_root)

    def write_fighters_xlsx(self, dst_root: Path = PROJECT_DATA):
        FighterJSONDataPayload(preloaded_data=self.data['fighters']).write_xlsx(dst_root=dst_root)

    def write_abilities_to_disk(self, dst: Path = Path(PROJECT_DATA, 'abilities.json')):
        self.validate_data()
        sorted_data = sorted(self.data['abilities'], key=lambda d: d['warband'])
        self._write_json(dst=dst, data=sorted_data)

    def write_warbands_to_disk(self, dst: Path = PROJECT_DATA):
        self.validate_data()
        old_cities = [
            'Anvilgard Loyalists',
            'The Phoenicium',
            'Greywater Fastness',
            "Tempest's Eye",
            'The Living City',
            'Hallowheart',
            'Hammerhal'
        ]

        # data is structured as
        # grand_alliance
        #  - faction_fighters.json
        #    - list of fighters (including bladeborn)
        #  - faction_abilities.json
        #    - list of abilities (including bladeborn)
        data_structure = {'universal': {'universal': {'abilities': list()}}}

        # bladeborn -> faction
        faction_mapping = {'universal': 'universal'}
        for c in old_cities:
            faction_mapping[c] = 'Cities of Sigmar'

        for fighter in self.data['fighters']:
            ga = fighter['grand_alliance']
            warband = fighter['warband']
            bladeborn = fighter['bladeborn']

            if warband in old_cities:
                warband = 'Cities of Sigmar'

            if ga not in data_structure.keys():
                data_structure[ga] = dict()
            if warband not in data_structure[ga].keys():
                data_structure[ga][warband] = {'fighters': list(), 'abilities': list()}
            data_structure[ga][warband]['fighters'].append(fighter)
            # add bladeborn warband to faction mapping to be used by abilities
            if bladeborn:
                faction_mapping.update({bladeborn: warband})
            faction_mapping.update({warband: warband})

        for ability in self.data['abilities']:
            faction = faction_mapping[ability['warband']]
            ga = None
            possible_ga = [x for x in data_structure.keys() if faction in data_structure[x].keys()]
            if len(possible_ga) == 1:
                ga = possible_ga[0]
            if not ga:
                raise RuntimeError(f'unable to identify Grand Alliance for ability: {ability}')
            data_structure[ga][faction]['abilities'].append(ability)

        for grand_alliance, warbands in data_structure.items():
            for warband, content in warbands.items():

                ability_path = Path(dst, grand_alliance, sanitise_filename(f'{warband}_abilities.json'))
                self._write_json(
                    dst=ability_path,
                    data=sorted(content['abilities'], key=lambda d: d['warband'])
                )

                if warband != 'universal':
                    fighter_path = Path(dst, grand_alliance, sanitise_filename(f'{warband}_fighters.json'))
                    self._write_json(
                        dst=fighter_path,
                        data=sort_fighters([dict(sorted(x.items())) for x in content['fighters']])
                    )

    def write_to_disk(self, dst_root: Path = PROJECT_DATA):
        self.write_fighters_to_disk(Path(dst_root, 'fighters.json'))
        self.write_abilities_to_disk(Path(dst_root, 'abilities.json'))
        self.write_warbands_to_disk(dst_root)

    def validate_data(self):
        with open(self.schema, 'r') as f:
            warband_schema = json.load(f)
        jsonschema.validate(self.data, warband_schema)
