"""
Temp file just used for local testing. Added to repo for personal ease.
"""

from data_parsing import FighterJSONPayload
from pathlib import Path

if __name__ == '__main__':
    src_data = Path(Path(__file__).parent.parent, 'data', 'fighters.json')
    data = FighterJSONPayload(src_file=src_data)
    data.write_warbands_to_disk()
    x = 1
