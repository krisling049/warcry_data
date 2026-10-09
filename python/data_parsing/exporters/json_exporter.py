import logging
from copy import deepcopy
from pathlib import Path

from ..constants import BATTLETRAIT
from ..fighters import sort_fighters
from ..models import write_data_json

logger = logging.getLogger(__name__)


def _by_warband(abilities: list[dict]) -> list[dict]:
    return sorted(abilities, key=lambda d: d['warband'])


def export_fighters(fighters_data: list[dict], dst: Path) -> None:
    logger.info(f'Exporting {len(fighters_data)} fighters to {dst}')
    write_data_json(dst=dst, data=sort_fighters([dict(sorted(f.items())) for f in fighters_data]))


def export_abilities(abilities_data: list[dict], dst: Path, exclude_battletraits: bool) -> None:
    data = [a for a in abilities_data if not (exclude_battletraits and a['cost'] == BATTLETRAIT)]
    logger.info(f'Exporting {len(data)} abilities to {dst}')
    write_data_json(dst=dst, data=_by_warband(data))


def export_battletraits(abilities_data: list[dict], dst: Path) -> None:
    data = [a for a in abilities_data if a['cost'] == BATTLETRAIT]
    logger.info(f'Exporting {len(data)} battletraits to {dst}')
    write_data_json(dst=dst, data=_by_warband(data))


def export_localized_abilities(abilities_data: list[dict], translations: dict[str, dict], dst: Path) -> None:
    """Write abilities with translated fields; untranslated abilities keep their English text."""
    data = deepcopy(abilities_data)
    for ability in data:
        ability.update(translations.get(ability['_id'], {}))
    untranslated = sum(1 for a in data if a['_id'] not in translations)
    logger.info(f'Exporting {len(data)} localised abilities to {dst} ({untranslated} untranslated)')
    write_data_json(dst=dst, data=_by_warband(data))
