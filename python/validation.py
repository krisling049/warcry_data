import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from data_parsing.data_loading import load_all_data
from data_parsing.models import PROJECT_DATA
from data_parsing.schema_validation import validate_data


@dataclass
class TypedArgs:
    data: Path


def parse_args() -> TypedArgs:
    parser = argparse.ArgumentParser(description='Report every validation error in the source data.')
    parser.add_argument('--data', type=Path, default=PROJECT_DATA, help='path to the source data folder')
    return TypedArgs(**vars(parser.parse_args()))


if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

    errors = validate_data(load_all_data(args.data))
    for error in errors:
        logging.error(error)
    if errors:
        sys.exit(f'validation failed: {len(errors)} errors')
    logging.info('validation passed')
