import argparse
import json
from pathlib import Path
from typing import Optional

import jsonschema

from data_parsing.abilities import ABILITY_SCHEMA
from data_parsing.factions import FACTION_SCHEMA
from data_parsing.fighters import FIGHTER_SCHEMA
from data_parsing.models import PROJECT_DATA
from data_parsing.warbands import WarbandsJSONDataPayload


def validate_data(data: list[dict], schemafile: Optional[Path] = None, schemadata: Optional[dict] = None):
    if not schemafile and not schemadata:
        raise RuntimeError('Must provide either schema file or schema data for validation')
    if schemafile:
        schemadata = json.loads(schemafile.read_text())
    jsonschema.validate(data, schemadata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=PROJECT_DATA,
        help="path to project data folder"
    )
    args = parser.parse_args()

    warband_data = WarbandsJSONDataPayload()
    ability_schema = json.loads(ABILITY_SCHEMA.read_text())
    fighter_schema = json.loads(FIGHTER_SCHEMA.read_text())
    faction_schema = json.loads(FACTION_SCHEMA.read_text())

    print(f'validating {len(warband_data.data["abilities"])} abilities')
    for ability in warband_data.data['abilities']:
        validate_data(data=ability, schemadata=ability_schema)
    print(f'validating {len(warband_data.data["fighters"])} fighters')
    for fighter in warband_data.data['fighters']:
        validate_data(data=fighter, schemadata=fighter_schema)
    print(f'validating {len(warband_data.data["factions"])} fighters')
    for faction in warband_data.data['factions']:
        validate_data(data=faction, schemadata=faction_schema)

    print('validation passed')


