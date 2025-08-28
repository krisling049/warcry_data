"""
Business rules and configurable logic for Warcry data processing.

This module centralizes business logic that was previously hardcoded,
making it configurable and extensible.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List

from .abilities import Ability
from .fighters import Fighter


class ExclusionRule(Protocol):
    """Protocol for rules that determine if an entity should be excluded."""
    
    def should_exclude(self, entity) -> bool:
        """Return True if entity should be excluded."""
        ...


class FighterExclusionRule(ABC):
    """Abstract base class for fighter exclusion rules."""
    
    @abstractmethod
    def should_exclude(self, fighter: Fighter) -> bool:
        """Return True if fighter should be excluded."""
        pass


class WarbandExclusionRule(FighterExclusionRule):
    """Excludes fighters based on warband name."""
    
    def __init__(self, excluded_warbands: List[str]):
        self.excluded_warbands = excluded_warbands
    
    def should_exclude(self, fighter: Fighter) -> bool:
        return fighter.warband in self.excluded_warbands


class PointsThresholdRule(FighterExclusionRule):
    """Excludes fighters above a certain points threshold."""
    
    def __init__(self, max_points: int):
        self.max_points = max_points
    
    def should_exclude(self, fighter: Fighter) -> bool:
        return fighter.points > self.max_points


class CompositeFighterExclusionRule(FighterExclusionRule):
    """Combines multiple exclusion rules using OR logic."""
    
    def __init__(self, rules: List[FighterExclusionRule]):
        self.rules = rules
    
    def should_exclude(self, fighter: Fighter) -> bool:
        return any(rule.should_exclude(fighter) for rule in self.rules)


class AbilityExclusionRule(ABC):
    """Abstract base class for ability exclusion rules."""
    
    @abstractmethod
    def should_exclude(self, ability: Ability) -> bool:
        """Return True if ability should be excluded."""
        pass


class AbilityCostExclusionRule(AbilityExclusionRule):
    """Excludes abilities based on cost type."""
    
    def __init__(self, excluded_costs: List[str]):
        self.excluded_costs = excluded_costs
    
    def should_exclude(self, ability: Ability) -> bool:
        return ability.cost in self.excluded_costs


class WarbandAbilityExclusionRule(AbilityExclusionRule):
    """Excludes abilities based on warband."""
    
    def __init__(self, excluded_warbands: List[str]):
        self.excluded_warbands = excluded_warbands
    
    def should_exclude(self, ability: Ability) -> bool:
        return ability.warband in self.excluded_warbands


class TTSExportRules:
    """Business rules specific to Tabletop Simulator export."""
    
    @classmethod
    def get_fighter_exclusion_rule(cls) -> FighterExclusionRule:
        """Get the composite rule for excluding fighters from TTS export."""
        return CompositeFighterExclusionRule([
            WarbandExclusionRule(["Cities of Sigmar"]),
            # Additional rules can be easily added here
            # PointsThresholdRule(1000),  # Example: exclude expensive fighters
        ])
    
    @classmethod
    def get_ability_exclusion_rule(cls) -> AbilityExclusionRule:
        """Get the composite rule for excluding abilities from TTS export."""
        from .constants import SpecialWarbands, AbilityCosts
        
        # For now, keep existing logic but make it configurable
        class TTSAbilityExclusionRule(AbilityExclusionRule):
            def should_exclude(self, ability: Ability) -> bool:
                return (ability.warband == SpecialWarbands.UNIVERSAL or 
                       ability.cost == AbilityCosts.BATTLETRAIT)
        
        return TTSAbilityExclusionRule()


class ValidationRules:
    """Business rules for data validation."""
    
    @staticmethod
    def is_valid_points_value(points: int) -> bool:
        """Check if points value is within valid range."""
        return 0 <= points <= 2000
    
    @staticmethod
    def is_valid_movement(movement: int) -> bool:
        """Check if movement value is realistic."""
        return 1 <= movement <= 50
    
    @staticmethod
    def is_valid_toughness(toughness: int) -> bool:
        """Check if toughness value is within valid range."""
        return 1 <= toughness <= 20
    
    @staticmethod
    def is_valid_wounds(wounds: int) -> bool:
        """Check if wounds value is within valid range."""
        return 1 <= wounds <= 300


class ConfigurableRuleEngine:
    """Engine for applying configurable business rules."""
    
    def __init__(self):
        self.fighter_exclusion_rules: List[FighterExclusionRule] = []
        self.ability_exclusion_rules: List[AbilityExclusionRule] = []
    
    def add_fighter_exclusion_rule(self, rule: FighterExclusionRule) -> None:
        """Add a fighter exclusion rule."""
        self.fighter_exclusion_rules.append(rule)
    
    def add_ability_exclusion_rule(self, rule: AbilityExclusionRule) -> None:
        """Add an ability exclusion rule."""
        self.ability_exclusion_rules.append(rule)
    
    def should_exclude_fighter(self, fighter: Fighter) -> bool:
        """Check if fighter should be excluded based on all rules."""
        return any(rule.should_exclude(fighter) for rule in self.fighter_exclusion_rules)
    
    def should_exclude_ability(self, ability: Ability) -> bool:
        """Check if ability should be excluded based on all rules."""
        return any(rule.should_exclude(ability) for rule in self.ability_exclusion_rules)
    
    def filter_fighters(self, fighters: List[Fighter]) -> List[Fighter]:
        """Filter fighters based on exclusion rules."""
        return [f for f in fighters if not self.should_exclude_fighter(f)]
    
    def filter_abilities(self, abilities: List[Ability]) -> List[Ability]:
        """Filter abilities based on exclusion rules."""
        return [a for a in abilities if not self.should_exclude_ability(a)]
