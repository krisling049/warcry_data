from data_parsing.warbands import WarbandsJSONDataPayload
from data_parsing.models import DIST, LOCALISATION_DATA
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
    combined_data.write_tts_fighters(dst=Path(DIST, 'fighters_tts.json'))
    combined_data.write_fighters_html(dst_root=DIST)
    for file in LOCALISATION_DATA.iterdir():
        lang = file.stem
        combined_data.write_localised_data(dst=Path(DIST, lang, 'abilities.json'), loc_file=file)

    print('done')
