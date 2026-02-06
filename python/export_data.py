import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from data_parsing.pipeline import load_warband_data, process_warband_data, export_all_with_localization
from data_parsing.config import DIST, LOCAL_DATA, PROJECT_ROOT


@dataclass
class TypedArgs:
    local: bool


def parse_args() -> TypedArgs:

    parser = argparse.ArgumentParser()
    parser.add_argument('-local', action='store_true', help='export data to untracked folder instead of docs')
    return TypedArgs(**vars(parser.parse_args()))


if __name__ == '__main__':
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(name)s - %(message)s'
    )

    out_dir = LOCAL_DATA if args.local else DIST

    # Load and process data
    schema_path = Path(PROJECT_ROOT, 'schemas', 'warband_schema.json')
    data = load_warband_data(schema=schema_path)
    warband_data = process_warband_data(data)
    export_all_with_localization(warband_data, data, out_dir)

    print('done')
