"""
Validation configuration for Warcry data processing.

Simple dataclass-based rules for TTS export filtering and data validation.
"""

from dataclasses import dataclass, field
from typing import List

from .config import SpecialWarbands, AbilityCosts
from .models import Ability, Fighter


@dataclass
class TTSExportRules:
    """Configurable rules for TTS export filtering."""
    excluded_warbands: List[str] = field(default_factory=lambda: ["Cities of Sigmar"])
    excluded_ability_costs: List[str] = field(default_factory=lambda: [AbilityCosts.BATTLETRAIT])
    exclude_universal_abilities: bool = True

    def should_exclude_fighter(self, fighter: Fighter) -> bool:
        return fighter.warband in self.excluded_warbands

    def should_exclude_ability(self, ability: Ability) -> bool:
        if self.exclude_universal_abilities and ability.warband == SpecialWarbands.UNIVERSAL:
            return True
        return ability.cost in self.excluded_ability_costs


@dataclass
class ValidationRules:
    """Configurable ranges for data validation."""
    max_points: int = 2000
    min_points: int = 0
    min_movement: int = 1
    max_movement: int = 50
    min_toughness: int = 1
    max_toughness: int = 20
    min_wounds: int = 1
    max_wounds: int = 300

    def is_valid_points_value(self, points: int) -> bool:
        return self.min_points <= points <= self.max_points

    def is_valid_movement(self, movement: int) -> bool:
        return self.min_movement <= movement <= self.max_movement

    def is_valid_toughness(self, toughness: int) -> bool:
        return self.min_toughness <= toughness <= self.max_toughness

    def is_valid_wounds(self, wounds: int) -> bool:
        return self.min_wounds <= wounds <= self.max_wounds
