import argparse
import logging
import sys
from pathlib import Path

from data_parsing.config import SchemaFiles, PROJECT_DATA, PROJECT_ROOT
from data_parsing.pipeline import load_warband_data
from data_parsing.io import validate_against_schema


def get_duplicate_ids(to_check: list[dict]) -> list[str]:
    all_ids = [i["_id"] for i in to_check]
    return [i for i in all_ids if all_ids.count(i) != 1]


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

    # Load data using functional approach
    schema_path = Path(PROJECT_ROOT, 'schemas', 'warband_schema.json')
    data = load_warband_data(src=args.data, schema=schema_path)

    validation_pass = True

    logging.info(f'validating {len(data["abilities"])} abilities')
    ability_dupes = get_duplicate_ids(data['abilities'])
    for ability in data['abilities']:
        if ability["_id"] in ability_dupes:
            logging.error(f'validation failure: duplicate id: {ability["warband"]}/{ability["name"]}: {ability["_id"]}')
            validation_pass = False
        validate_against_schema(data=ability, schema_path=SchemaFiles.ABILITY)

    logging.info(f'validating {len(data["fighters"])} fighters')
    fighter_dupes = get_duplicate_ids(data['fighters'])
    for fighter in data['fighters']:
        if fighter["_id"] in fighter_dupes:
            logging.error(f'validation failure: duplicate id: {fighter["grand_alliance"]}/{fighter["warband"]}/{fighter["name"]}: {fighter["_id"]}')
            validation_pass = False
        validate_against_schema(data=fighter, schema_path=SchemaFiles.FIGHTER)

    logging.info(f'validating {len(data["factions"])} factions')
    for faction in data['factions']:
        validate_against_schema(data=faction, schema_path=SchemaFiles.FACTION)

    if validation_pass:
        logging.info('validation passed')
    else:
        sys.exit('validation failed')
