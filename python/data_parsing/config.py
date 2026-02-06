"""
Configuration constants for Warcry data processing.

Centralizes all paths, schemas, enums and magic strings.
"""

from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_DATA = Path(PROJECT_ROOT, 'data')
DIST = Path(PROJECT_ROOT, 'docs')
LOCAL_DATA = Path(PROJECT_ROOT, 'local', 'data')
LOCALISATION_DATA = Path(PROJECT_ROOT, 'localisation')


class FileTypes(Enum):
    """File type suffixes for different data files."""
    FIGHTERS = "_fighters.json"
    ABILITIES = "_abilities.json"
    FACTION = "_faction.json"


class SchemaFiles:
    """Schema file paths."""
    ABILITY = PROJECT_ROOT / 'schemas' / 'ability_schema.json'
    ABILITIES_AGGREGATE = PROJECT_ROOT / 'schemas' / 'aggregate_ability_schema.json'
    FACTION = PROJECT_ROOT / 'schemas' / 'faction_schema.json'
    FIGHTER = PROJECT_ROOT / 'schemas' / 'fighter_schema.json'
    FIGHTERS_AGGREGATE = PROJECT_ROOT / 'schemas' / 'aggregate_fighter_schema.json'
    WARBAND = PROJECT_ROOT / 'schemas' / 'warband_schema.json'


class SpecialWarbands:
    """Special warband identifiers."""
    UNIVERSAL = "universal"


class AbilityCosts:
    """Ability cost types used in Warcry."""
    DOUBLE = "double"
    TRIPLE = "triple"
    QUAD = "quad"
    REACTION = "reaction"
    BATTLETRAIT = "battletrait"


class DataTypes:
    """Data type identifiers."""
    FIGHTERS = "fighters"
    ABILITIES = "abilities"
    FACTIONS = "factions"
