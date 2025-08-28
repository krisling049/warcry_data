import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from data_parsing.models import DIST, LOCALISATION_DATA, LOCAL_DATA
from data_parsing.warband_pipeline import WarbandDataPipeline


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

    combined_data = WarbandDataPipeline()
    combined_data.export_abilities_json(dst=Path(out_dir, 'abilities.json'), exclude_battletraits=True)
    combined_data.export_battletraits_json(dst=Path(out_dir, 'battletraits.json'))
    combined_data.export_abilities_json(dst=Path(out_dir, 'abilities_battletraits.json'), exclude_battletraits=False)
    combined_data.export_fighters_json(dst=Path(out_dir, 'fighters.json'))
    combined_data.export_tts_fighters(dst=Path(out_dir, 'fighters_tts.json'))
    combined_data.export_fighters_html(dst_root=out_dir)
    combined_data.export_fighters_csv(dst_root=out_dir)
    for file in LOCALISATION_DATA.iterdir():
        if file.is_file() and file.suffix == '.json':
            lang = file.stem
            combined_data.export_localized_data(loc_file=file, dst=Path(out_dir, lang, 'abilities.json'))

    print('done')
