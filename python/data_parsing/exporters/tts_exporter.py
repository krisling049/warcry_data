import logging
from pathlib import Path

from ..abilities import Ability
from ..constants import BATTLETRAIT, TTS_EXCLUDED_WARBANDS, UNIVERSAL
from ..fighters import Fighter
from ..models import write_data_json

logger = logging.getLogger(__name__)


def _in_tts(ability: Ability) -> bool:
    return ability.warband != UNIVERSAL and ability.cost != BATTLETRAIT


def export_fighters(fighters: list[Fighter], dst: Path) -> None:
    tts_data = []
    for fighter in fighters:
        if fighter.warband in TTS_EXCLUDED_WARBANDS:
            continue
        fighter_data = fighter.as_dict()
        fighter_data['abilities'] = [a.tts_format() for a in fighter.abilities if _in_tts(a)]
        tts_data.append(fighter_data)
    logger.info(f'Exporting {len(tts_data)} fighters to TTS format at {dst}')
    write_data_json(dst=dst, data=tts_data)
