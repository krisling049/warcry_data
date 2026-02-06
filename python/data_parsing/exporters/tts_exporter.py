"""
Tabletop Simulator (TTS) export functionality for Warcry data.

Accepts typed Fighter objects with abilities already assigned by the pipeline.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from ..business_rules import TTSExportRules
from ..models import Fighter
from ..io import write_data_json

logger = logging.getLogger(__name__)

# Module-level rules instance
TTS_RULES = TTSExportRules()


def convert_to_tts_format(fighters: List[Fighter]) -> List[Dict[str, Any]]:
    """Convert typed fighters to TTS format.

    Args:
        fighters: List of Fighter objects (with abilities already assigned)

    Returns:
        List of fighters in TTS format
    """
    tts_data = []
    excluded_count = 0

    for fighter in fighters:
        if TTS_RULES.should_exclude_fighter(fighter):
            excluded_count += 1
            continue

        fighter_data = fighter.to_dict()

        # Convert abilities to TTS format, filtering excluded abilities
        tts_abilities = [
            ability.tts_format()
            for ability in fighter.abilities
            if not TTS_RULES.should_exclude_ability(ability)
        ]
        fighter_data['abilities'] = tts_abilities

        tts_data.append(fighter_data)

    logger.info(f"Converted {len(tts_data)} fighters to TTS format ({excluded_count} excluded)")
    return tts_data


def export_tts_fighters(fighters: List[Fighter], dst: Path) -> None:
    """Export fighters in TTS format.

    Args:
        fighters: List of Fighter objects (with abilities already assigned)
        dst: Destination file path
    """
    tts_data = convert_to_tts_format(fighters)
    logger.info(f"Exporting {len(tts_data)} fighters to TTS format at {dst}")
    write_data_json(dst=dst, data=tts_data)
