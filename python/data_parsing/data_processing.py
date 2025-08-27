"""
Data processing module for Warcry data.

Handles ID assignment, ability assignment, and faction assignment.
"""

import logging
import re
import uuid
from typing import List, Dict, Any

from .abilities import Ability
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
            data: Dictionary containing fighters, abilities, and factions data
        """
        placeholder_pattern = re.compile(r'^PLACEHOLDER.*|^XXXXXX.*', flags=re.IGNORECASE)

        for data_type, entities in data.items():
            for entity in entities:
                if all([data_type in ["fighters", "abilities"], '_id' not in entity or placeholder_pattern.match(entity.get('_id', ''))]):
                    new_id = str(uuid.uuid4()).split('-')[0]
                    logger.info(f'Assigning _id for {entity.get("name", "unnamed")} - {new_id}')
                    entity['_id'] = new_id

    def assign_abilities(self) -> None:
        """Assign abilities to fighters based on warband and runemarks."""
        logger.info("Starting ability assignment")
        assignments_made = 0
        
        for ability in self.abilities:
            faction_match = [
                fighter for fighter in self.fighters.fighters 
                if ability.warband in [fighter.warband, fighter.subfaction_runemark(), 'universal']
            ]
            
            for fighter in faction_match:
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
