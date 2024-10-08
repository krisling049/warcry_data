import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

from data_parsing.models import DIST, LOCALISATION_DATA, LOCAL_DATA
from data_parsing.warbands import WarbandsJSONDataPayload


def get_data_files(data_loc: Path = DIST) -> List[Path]:
    to_ret = list()
    for ga in ['chaos', 'death', 'destruction', 'order', 'universal']:
        for file in Path(data_loc, ga).iterdir():
            if file.is_file():
                to_ret.append(file)
    return to_ret


@dataclass
class TypedArgs:
    local: bool


def parse_args() -> TypedArgs:

    parser = argparse.ArgumentParser()
    parser.add_argument('-local', action='store_true', help='export data to untracked folder instead of docs')
    return TypedArgs(**vars(parser.parse_args()))


if __name__ == '__main__':
    args = parse_args()

    out_dir = LOCAL_DATA if args.local else DIST

    combined_data = WarbandsJSONDataPayload()
    combined_data.write_abilities_to_disk(dst=Path(out_dir, 'abilities.json'), exclude_battletraits=True)
    combined_data.write_battletraits_to_disk(dst=Path(out_dir, 'battletraits.json'))
    combined_data.write_abilities_to_disk(dst=Path(out_dir, 'abilities_battletraits.json'), exclude_battletraits=False)
    combined_data.write_fighters_to_disk(dst=Path(out_dir, 'fighters.json'))
    combined_data.write_tts_fighters(dst=Path(out_dir, 'fighters_tts.json'))
    combined_data.write_fighters_html(dst_root=out_dir)
    combined_data.write_fighters_csv(dst_root=out_dir)
    for file in LOCALISATION_DATA.iterdir():
        lang = file.stem
        combined_data.write_localised_data(dst=Path(out_dir, lang, 'abilities.json'), loc_file=file)

    print('done')
