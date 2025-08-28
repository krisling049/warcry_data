"""
Data processing module for Warcry data.

Handles ID assignment, ability assignment and faction assignment.
"""

import logging
import re
import uuid
from collections import defaultdict
from typing import List, Dict, Any

from .abilities import Ability
from .constants import SpecialWarbands, DataTypes
from .factions import Factions
from .fighters import Fighters

logger = logging.getLogger(__name__)


class WarbandDataProcessor:
    """Handles processing and assignment operations on warband data."""
    
    def __init__(self, fighters: Fighters, abilities: List[Ability], factions: Factions):
        self.fighters = fighters
        self.abilities = abilities
        self.factions = factions
    
    def assign_ids(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Assign unique IDs to entities that don't have them.
        
        Args:
            data: Dictionary containing fighters, abilities and factions data
        """
        placeholder_pattern = re.compile(r'^PLACEHOLDER.*|^XXXXXX.*', flags=re.IGNORECASE)

        for data_type, entities in data.items():
            for entity in entities:
                valid_types = [DataTypes.FIGHTERS, DataTypes.ABILITIES]
                if all([data_type in valid_types, '_id' not in entity or placeholder_pattern.match(entity.get('_id', ''))]):
                    new_id = str(uuid.uuid4()).split('-')[0]
                    logger.info(f'Assigning _id for {entity.get("name", "unnamed")} - {new_id}')
                    entity['_id'] = new_id

    def assign_abilities(self) -> None:
        """Assign abilities to fighters based on warband and runemarks.
        
        Optimized implementation uses lookup tables to reduce complexity
        from O(n*m) to O(n+m) where n=abilities, m=fighters.
        """
        logger.info("Starting ability assignment")
        assignments_made = 0
        
        # Build lookup tables first - O(m) where m = fighters
        fighters_by_warband = defaultdict(list)
        fighters_by_subfaction = defaultdict(list)
        
        for fighter in self.fighters.fighters:
            fighters_by_warband[fighter.warband].append(fighter)
            subfaction = fighter.subfaction_runemark()
            if subfaction:
                fighters_by_subfaction[subfaction].append(fighter)
        
        # Assign abilities - O(n * f) where f = fighters per warband (much smaller than total)
        for ability in self.abilities:
            target_fighters = []
            
            if ability.warband == SpecialWarbands.UNIVERSAL:
                target_fighters = self.fighters.fighters
            else:
                # Get fighters from both warband and subfaction lookups
                target_fighters.extend(fighters_by_warband.get(ability.warband, []))
                target_fighters.extend(fighters_by_subfaction.get(ability.warband, []))
            
            for fighter in target_fighters:
                if set(ability.runemarks).issubset(set(fighter.runemarks)):
                    fighter.abilities.append(ability)
                    assignments_made += 1
        
        logger.info(f"Completed ability assignment: {assignments_made} assignments made")

    def assign_factions(self) -> None:
        """Assign factions and subfactions to fighters."""
        logger.info("Starting faction assignment")
        assignments_made = 0
        
        for fighter in self.fighters.fighters:
            for faction in self.factions.factions:
                if fighter.warband == faction.warband:
                    fighter.faction = faction
                    assignments_made += 1
                    
                    # Assign subfactions
                    for subfaction in faction.subfactions:
                        runemarks_to_check = [*fighter.runemarks, fighter.as_dict().get('subfaction')]
                        if any(runemark for runemark in runemarks_to_check 
                              if runemark and runemark == subfaction.runemark):
                            fighter.subfaction = subfaction
                            break
        
        logger.info(f"Completed faction assignment: {assignments_made} assignments made")

    def process_all(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Run all processing steps in the correct order.
        
        Args:
            data: Raw data dictionary to process
        """
        logger.info("Starting data processing pipeline")
        
        # Step 1: Assign IDs
        self.assign_ids(data)
        
        # Step 2: Assign factions (must come before abilities)
        self.assign_factions()
        
        # Step 3: Assign abilities
        self.assign_abilities()
        
        logger.info("Data processing pipeline completed")
