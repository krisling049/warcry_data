import logging
from pathlib import Path

from .constants import ABILITIES, FACTIONS, FIGHTERS, FILE_SUFFIXES
from .models import load_json_file

logger = logging.getLogger(__name__)

WarbandData = dict[str, list[dict]]


def load_all_data(src: Path) -> WarbandData:
    if not src.is_dir():
        raise FileNotFoundError(f'data folder not found: {src}')

    data: WarbandData = {FIGHTERS: [], ABILITIES: [], FACTIONS: []}
    # Sorted so that every export lists entities in the same order on every OS.
    for file in sorted(src.rglob('*.json'), key=lambda p: p.as_posix()):
        if file.name.endswith(FILE_SUFFIXES[FIGHTERS]):
            data[FIGHTERS].extend(load_json_file(file))
        elif file.name.endswith(FILE_SUFFIXES[ABILITIES]):
            data[ABILITIES].extend(load_json_file(file))
        elif file.name.endswith(FILE_SUFFIXES[FACTIONS]):
            data[FACTIONS].append(load_json_file(file))

    logger.info(f'Loaded {len(data[FIGHTERS])} fighters, {len(data[ABILITIES])} abilities, '
                f'{len(data[FACTIONS])} factions from {src}')
    return data
