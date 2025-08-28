"""
Tabletop Simulator (TTS) export functionality for Warcry data.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from ..business_rules import TTSExportRules
from ..fighters import Fighter, Fighters
from ..models import write_data_json

logger = logging.getLogger(__name__)


class TTSExporter:
    """Handles Tabletop Simulator export operations."""
    
    def __init__(self):
        """Initialize with TTS-specific business rules."""
        self.fighter_exclusion_rule = TTSExportRules.get_fighter_exclusion_rule()
        self.ability_exclusion_rule = TTSExportRules.get_ability_exclusion_rule()
    
    def should_exclude_from_tts(self, fighter: Fighter) -> bool:
        """Determine if a fighter should be excluded from TTS export.
        
        Args:
            fighter: Fighter object to check
            
        Returns:
            True if fighter should be excluded
        """
        return self.fighter_exclusion_rule.should_exclude(fighter)
    
    def convert_to_tts_format(self, fighters: Fighters) -> List[Dict[str, Any]]:
        """Convert fighters to TTS format.
        
        Args:
            fighters: Fighters collection
            
        Returns:
            List of fighters in TTS format
        """
        tts_data = []
        excluded_count = 0
        
        for fighter in fighters.fighters:
            if self.should_exclude_from_tts(fighter):
                excluded_count += 1
                continue
                
            fighter_data = fighter.as_dict()
            
            # Convert abilities to TTS format using business rules
            tts_abilities = [
                ability.tts_format() 
                for ability in fighter.abilities 
                if not self.ability_exclusion_rule.should_exclude(ability)
            ]
            fighter_data['abilities'] = tts_abilities
            
            tts_data.append(fighter_data)
        
        logger.info(f"Converted {len(tts_data)} fighters to TTS format ({excluded_count} excluded)")
        return tts_data
    
    def export_fighters(self, fighters: Fighters, dst: Path) -> None:
        """Export fighters in TTS format.
        
        Args:
            fighters: Fighters collection
            dst: Destination file path
        """
        tts_data = self.convert_to_tts_format(fighters)
        logger.info(f"Exporting {len(tts_data)} fighters to TTS format at {dst}")
        write_data_json(dst=dst, data=tts_data)
