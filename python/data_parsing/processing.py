"""
Pure data processing functions for warband data enrichment.

Handles ID assignment, ability assignment, and faction assignment.
"""

import logging
import re
import uuid
from collections import defaultdict
from typing import Dict, List, Any

from .config import DataTypes, SpecialWarbands
from .models import Ability, Faction, Fighter

logger = logging.getLogger(__name__)


def assign_ids(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Assign unique IDs to entities that don't have them.

    Mutates the data dictionary in place.

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


def assign_abilities(fighters: List[Fighter], abilities: List[Ability]) -> None:
    """Assign abilities to fighters based on warband and runemarks.

    Uses lookup tables for O(n+m) performance.
    Mutates fighter objects in place.

    Args:
        fighters: List of Fighter objects
        abilities: List of Ability objects
    """
    logger.info("Starting ability assignment")
    assignments_made = 0

    fighters_by_warband = defaultdict(list)
    fighters_by_subfaction = defaultdict(list)

    for fighter in fighters:
        fighters_by_warband[fighter.warband].append(fighter)
        subfaction = fighter.subfaction_runemark()
        if subfaction:
            fighters_by_subfaction[subfaction].append(fighter)

    for ability in abilities:
        target_fighters = []

        if ability.warband == SpecialWarbands.UNIVERSAL:
            target_fighters = fighters
        else:
            target_fighters.extend(fighters_by_warband.get(ability.warband, []))
            target_fighters.extend(fighters_by_subfaction.get(ability.warband, []))

        for fighter in target_fighters:
            if set(ability.runemarks).issubset(set(fighter.runemarks)):
                fighter.abilities.append(ability)
                assignments_made += 1

    logger.info(f"Completed ability assignment: {assignments_made} assignments made")


def assign_factions(fighters: List[Fighter], factions: List[Faction]) -> None:
    """Assign factions and subfactions to fighters.

    Mutates fighter objects in place.

    Args:
        fighters: List of Fighter objects
        factions: List of Faction objects
    """
    logger.info("Starting faction assignment")
    assignments_made = 0

    for fighter in fighters:
        for faction in factions:
            if fighter.warband == faction.warband:
                fighter.faction = faction
                assignments_made += 1

                for subfaction in faction.subfactions:
                    runemarks_to_check = [*fighter.runemarks, fighter._subfaction_str]
                    if any(runemark for runemark in runemarks_to_check
                          if runemark and runemark == subfaction.runemark):
                        fighter.subfaction = subfaction
                        break

    logger.info(f"Completed faction assignment: {assignments_made} assignments made")
