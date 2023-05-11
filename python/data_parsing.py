from pathlib import Path
import json
from typing import List, Dict


def sort_data(data_to_sort: List[Dict]) -> List[Dict]:
    sorted_data = sorted(
        data_to_sort,
        key=lambda x: (
            x['grand_alliance'],
            x['warband'],
            x['bladeborn'],
            x['points']
        )
    )

    return sorted_data


class DataPayload:
    """
    The template for handling data. Can be subclassed for other data types (xlsx) in future. Currently intended to
    load data from a single data file (e.g. data/fighters.json).
    """

    def __init__(self, src_file: Path, src_format: str = None):
        self.src_file = src_file
        self.src_format = src_format if src_format else src_file.suffix  # xlsx, json, csv etc
        self.data = self.load_data()

    @classmethod
    def load_data(cls):
        raise NotImplementedError('class requires a load_data class method')

    @classmethod
    def write_to_disk(cls, dst: Path):
        raise NotImplementedError('class requires a write_to_disk class method')


# noinspection PyAbstractClass
class FighterDataPayload(DataPayload):

    @classmethod
    def write_warbands_to_disk(cls, dst_root):
        raise NotImplementedError('class requires a write_warbands_to_disk class method')


class FighterJSONPayload(FighterDataPayload):

    def load_data(self) -> List[Dict]:
        # We treat the fighters.json file as our source of truth so this is the one we load
        with open(self.src_file, 'r') as f:
            data = json.load(f)
        return data

    def write_aggregate_file_to_disk(self, dst: Path = Path(Path(__file__).parent.parent, 'data', 'fighters.json')):
        with open(dst, 'w') as nf:
            print(f'Writing {len(self.data)} fighters to {dst}...')
            json.dump(sort_data(self.data), nf, ensure_ascii=True, indent=4, sort_keys=False)

    def write_warbands_to_disk(self, dst_root: Path = Path(Path(__file__).parent.parent, 'data')):

        warband_by_ga = dict()

        for fighter in self.data:
            if fighter['grand_alliance'] not in warband_by_ga.keys():
                warband_by_ga[fighter['grand_alliance']] = dict()
            if fighter['warband'] not in warband_by_ga[fighter['grand_alliance']].keys():
                warband_by_ga[fighter['grand_alliance']][fighter['warband']] = list()
            warband_by_ga[fighter['grand_alliance']][fighter['warband']].append(fighter)

        for GA, WARBANDS in warband_by_ga.items():
            for warband, fighters in WARBANDS.items():
                data_path = Path(dst_root, GA.lower())
                filename = warband.lower().replace(' ', '_') + '.json'
                data_path.mkdir(parents=True, exist_ok=True)
                output_file = Path(data_path, filename)
                with open(output_file, 'w') as f:
                    print(f'Writing {len(WARBANDS[warband])} fighters to {output_file}...')
                    sorted_warband = sort_data(WARBANDS[warband])
                    json.dump(sorted_warband, f, ensure_ascii=True, indent=4, sort_keys=False)
