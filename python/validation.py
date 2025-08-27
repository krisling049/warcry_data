import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import jsonschema

from data_parsing.abilities import ABILITY_SCHEMA
from data_parsing.factions import FACTION_SCHEMA
from data_parsing.fighters import FIGHTER_SCHEMA
from data_parsing.models import PROJECT_DATA
from data_parsing.warbands import WarbandsJSONDataPayload


def get_duplicate_ids(to_check: list[dict]) -> list[str]:
    all_ids = [i["_id"] for i in to_check]
    return [i for i in all_ids if all_ids.count(i) != 1]


def validate_data(data: list[dict], schemafile: Optional[Path] = None, schemadata: Optional[dict] = None):
    if not schemafile and not schemadata:
        raise RuntimeError('Must provide either schema file or schema data for validation')
    if schemafile:
        schemadata = json.loads(schemafile.read_text())
    jsonschema.validate(data, schemadata)


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(name)s - %(message)s'
    )
    
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

    validation_pass = True

    logging.info(f'validating {len(warband_data.data["abilities"])} abilities')
    ability_dupes = get_duplicate_ids(warband_data.data['abilities'])
    for ability in warband_data.data['abilities']:
        if ability["_id"] in ability_dupes:
            logging.error(f'validation failure: duplicate id: {ability["warband"]}/{ability["name"]}: {ability["_id"]}')
            validation_pass = False
        validate_data(data=ability, schemadata=ability_schema)

    logging.info(f'validating {len(warband_data.data["fighters"])} fighters')
    fighter_dupes = get_duplicate_ids(warband_data.data['fighters'])
    for fighter in warband_data.data['fighters']:
        if fighter["_id"] in fighter_dupes:
            logging.error(f'validation failure: duplicate id: {fighter["grand_alliance"]}/{fighter["warband"]}/{fighter["name"]}: {fighter["_id"]}')
            validation_pass = False
        validate_data(data=fighter, schemadata=fighter_schema)

    logging.info(f'validating {len(warband_data.data["factions"])} factions')
    for faction in warband_data.data['factions']:
        validate_data(data=faction, schemadata=faction_schema)

    if validation_pass:
        logging.info('validation passed')
    else:
        sys.exit('validation failed')
