from data_parsing.warbands import WarbandDataPayload
from data_parsing.abilities import AbilityJSONDataPayload
from data_parsing.models import PROJECT_ROOT
from data_parsing.fighters import sort_fighters
from pathlib import Path
from typing import List
import json

def get_warband_files(data_loc: Path = PROJECT_ROOT) -> List[Path]:
    to_ret = list()
    for ga in ['chaos', 'death', 'destruction', 'order']:
        for file in Path(data_loc, ga).iterdir():
            if file.is_file():
                to_ret.append(file)
    return to_ret


if __name__ == '__main__':

    ability_data_payload = AbilityJSONDataPayload()
    ability_data_payload.write_to_disk()

    warbands = [WarbandDataPayload(warband_file=x) for x in get_warband_files(data_loc=Path(PROJECT_ROOT, 'data_tmp'))]
    fighters = list()
    for w in warbands:
        w.write_to_disk()
        fighters.extend(w.data['fighters'])

    fighters_out = Path(PROJECT_ROOT, 'data', 'fighters.json')

    with open(fighters_out, 'w') as f:
        print(f'Writing {len(fighters)} fighters to {fighters_out}...')
        sorted_fighters = [dict(sorted(x.items())) for x in fighters]
        json.dump(sort_fighters(sorted_fighters), f, ensure_ascii=False, indent=4, sort_keys=False)

    print('done')