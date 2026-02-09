"""
Tabletop Simulator (TTS) export functionality for Warcry data.

Accepts typed Fighter objects with abilities already assigned by the pipeline.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from ..validation_config import TTSExportRules
from ..models import Fighter
from ..io import write_data_json

logger = logging.getLogger(__name__)


def convert_to_tts_format(fighters: List[Fighter], rules: TTSExportRules = TTSExportRules()) -> List[Dict[str, Any]]:
    """Convert typed fighters to TTS format.

    Args:
        fighters: List of Fighter objects (with abilities already assigned)
        rules: TTS export rules

    Returns:
        List of fighters in TTS format
    """
    tts_data = []
    excluded_count = 0

    for fighter in fighters:
        if rules.should_exclude_fighter(fighter):
            excluded_count += 1
            continue

        fighter_data = fighter.to_dict()

        # Convert abilities to TTS format, filtering excluded abilities
        tts_abilities = [
            ability.tts_format()
            for ability in fighter.abilities
            if not rules.should_exclude_ability(ability)
        ]
        fighter_data['abilities'] = tts_abilities

        tts_data.append(fighter_data)

    logger.info(f"Converted {len(tts_data)} fighters to TTS format ({excluded_count} excluded)")
    return tts_data


def export_tts_fighters(fighters: List[Fighter], dst: Path, rules: TTSExportRules = TTSExportRules()) -> None:
    """Export fighters in TTS format.

    Args:
        fighters: List of Fighter objects (with abilities already assigned)
        dst: Destination file path
        rules: TTS export rules (defaults to TTSExportRules())
    """
    tts_data = convert_to_tts_format(fighters, rules=rules)
    logger.info(f"Exporting {len(tts_data)} fighters to TTS format at {dst}")
    write_data_json(dst=dst, data=tts_data)
