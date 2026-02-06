"""
Tabular export functionality for Warcry data.

HTML, CSV, XLSX and Markdown exports of fighter data.
"""

from copy import deepcopy
from pathlib import Path
from typing import List, Dict

import pandas as pd


def fighters_to_dataframe(fighters: List[Dict]) -> pd.DataFrame:
    """Convert fighter data to pandas DataFrame with flattened weapon data."""
    temp_data = deepcopy(fighters)
    for fighter in temp_data:
        for i, w in enumerate(fighter['weapons']):
            for k, v in w.items():
                fighter[f'weapon_{i + 1}_{k}'] = v
        del fighter['weapons']

    return pd.DataFrame(temp_data)


def export_fighters_html(fighters: List[Dict], dst_root: Path) -> None:
    """Export fighters to HTML table format."""
    out_file = Path(dst_root, 'fighters.html')
    df = fighters_to_dataframe(fighters)
    print(f'writing {out_file.absolute()}')
    df.to_html(out_file)


def export_fighters_csv(fighters: List[Dict], dst_root: Path) -> None:
    """Export fighters to CSV format."""
    out_file = Path(dst_root, 'fighters.csv')
    df = fighters_to_dataframe(fighters)
    print(f'writing {out_file.absolute()}')
    df.to_csv(out_file)


def export_fighters_xlsx(fighters: List[Dict], dst_root: Path) -> None:
    """Export fighters to Excel format."""
    out_file = Path(dst_root, 'fighters.xlsx')
    df = fighters_to_dataframe(fighters)
    print(f'writing {out_file.absolute()}')
    df.to_excel(out_file, engine='xlsxwriter')


def export_fighters_markdown(fighters: List[Dict], dst_root: Path) -> None:
    """Export fighters to Markdown table format."""
    out_file = Path(dst_root, 'fighters.md')
    df = fighters_to_dataframe(fighters)
    print(f'writing {out_file.absolute()}')
    df.to_markdown(out_file)
