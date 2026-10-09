import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from data_parsing.models import DIST, PROJECT_DATA
from data_parsing.warband_pipeline import WarbandDataPipeline


@dataclass
class TypedArgs:
    data: Path
    out: Path


def parse_args() -> TypedArgs:
    parser = argparse.ArgumentParser(description='Validate data/ and write all published files.')
    parser.add_argument('--data', type=Path, default=PROJECT_DATA, help='path to the source data folder')
    parser.add_argument('--out', type=Path, default=DIST, help='folder to write the published files to')
    return TypedArgs(**vars(parser.parse_args()))


if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
    WarbandDataPipeline(src=args.data).export_all(dst=args.out)
    logging.info(f'Exported to {args.out}')
