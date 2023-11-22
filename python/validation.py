import pathlib
import argparse
from data_parsing.models import PROJECT_DATA
from data_parsing.fighters import FighterJSONDataPayload
from data_parsing.abilities import AbilityJSONDataPayload
from data_parsing.warbands import WarbandsJSONDataPayload


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=pathlib.Path,
        default=PROJECT_DATA,
        help="path to project data folder"
    )
    args = parser.parse_args()

    to_validate = [
        FighterJSONDataPayload(),
        AbilityJSONDataPayload(),
        WarbandsJSONDataPayload()
    ]

    for data in to_validate:
        print(f'validating {data}')
        data.validate_data()

    print('validation passed')


