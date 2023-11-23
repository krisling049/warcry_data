from data_parsing.warbands import WarbandsJSONDataPayload
from data_parsing.models import DIST
from pathlib import Path
from typing import List


def get_data_files(data_loc: Path = DIST) -> List[Path]:
    to_ret = list()
    for ga in ['chaos', 'death', 'destruction', 'order', 'universal']:
        for file in Path(data_loc, ga).iterdir():
            if file.is_file():
                to_ret.append(file)
    return to_ret


if __name__ == '__main__':

    combined_data = WarbandsJSONDataPayload()
    combined_data.write_abilities_to_disk(dst=Path(DIST, 'abilities.json'))
    combined_data.write_fighters_to_disk(dst=Path(DIST, 'fighters.json'))

    print('done')
