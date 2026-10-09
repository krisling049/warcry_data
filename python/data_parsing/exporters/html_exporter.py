import logging
from copy import deepcopy
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def fighters_dataframe(fighters_data: list[dict]) -> pd.DataFrame:
    """One row per fighter, with weapons flattened into weapon_<n>_<field> columns."""
    rows = deepcopy(fighters_data)
    for fighter in rows:
        for i, weapon in enumerate(fighter.pop('weapons')):
            for k, v in weapon.items():
                fighter[f'weapon_{i + 1}_{k}'] = v
    return pd.DataFrame(rows)


def export_fighters_html(fighters_data: list[dict], dst: Path) -> None:
    logger.info(f'Exporting {len(fighters_data)} fighters to {dst}')
    fighters_dataframe(fighters_data).to_html(dst)


def export_fighters_csv(fighters_data: list[dict], dst: Path) -> None:
    logger.info(f'Exporting {len(fighters_data)} fighters to {dst}')
    fighters_dataframe(fighters_data).to_csv(dst)
