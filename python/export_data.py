from data_parsing.fighters import FighterJSONDataPayload
from data_parsing.abilities import AbilityJSONDataPayload
from data_parsing.warbands import WarbandsJSONDataPayload
from data_parsing.models import PROJECT_DATA
from data_parsing.fighters import sort_fighters
from pathlib import Path
from typing import List
import json


def get_data_files(data_loc: Path = PROJECT_DATA) -> List[Path]:
    to_ret = list()
    for ga in ['chaos', 'death', 'destruction', 'order', 'universal']:
        for file in Path(data_loc, ga).iterdir():
            if file.is_file():
                to_ret.append(file)
    return to_ret


if __name__ == '__main__':

    combined_data = WarbandsJSONDataPayload()
    combined_data.write_to_disk()

    print('done')
