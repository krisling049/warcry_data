import json
import pathlib
import jsonschema
import argparse
from typing import List, Dict, Union


def validate_data(data: Union[List[Dict], pathlib.Path], schema: Dict) -> bool:
    if isinstance(data, pathlib.Path):
        with open(data, 'r') as f:
            data = json.load(f)

    try:
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.ValidationError as ve:
        failing_fighter = data[ve.absolute_path[0]]['name']
        print(f'ERROR: {failing_fighter}', flush=True)
        raise ve
    # If we reach this point, the data has validated successfully, so we can return
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=pathlib.Path,
        default=pathlib.Path(pathlib.Path(__file__).parent.parent, 'data', 'fighters.json'),
        help="absolute path to json to be validated"
    )
    parser.add_argument(
        "--schema",
        type=pathlib.Path,
        default=pathlib.Path(pathlib.Path(__file__).parent.parent, 'data', 'schemas', 'aggregate_fighter_schema.json'),
        help="absolute path to schema file"
    )
    args = parser.parse_args()

    print(f'Loading schema: {args.schema.absolute()}')
    with open(args.schema.absolute(), 'r') as s:
        loaded_schema = json.load(s)

    print(f'Validating {args.data.name} using {args.schema.name}...')

    if validate_data(args.data, loaded_schema):
        print('Validation passed.')


