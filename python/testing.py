from data_parsing import JSONPayload
from pathlib import Path

if __name__ == '__main__':
    src_data = Path(Path(__file__).parent.parent, 'data', 'fighters.json')
    data = JSONPayload(src_file=src_data)
    data.load_data()
    x = 1