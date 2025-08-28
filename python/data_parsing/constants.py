"""
Constants for Warcry data processing.

Centralizes all magic strings and hardcoded values to improve maintainability.
"""

from enum import Enum

from .models import PROJECT_ROOT


class FileTypes(Enum):
    """File type suffixes for different data files."""
    FIGHTERS = "_fighters.json"
    ABILITIES = "_abilities.json" 
    FACTION = "_faction.json"


class GrandAlliances(Enum):
    """Grand Alliance names."""
    CHAOS = "chaos"
    DEATH = "death"
    DESTRUCTION = "destruction"
    ORDER = "order"
    UNIVERSAL = "universal"


class Encodings(Enum):
    """Text encoding options."""
    UTF8 = "utf-8"
    LATIN1 = "latin-1"  # Legacy fallback


class FolderNames:
    """Standard folder names."""
    SCHEMAS = "schemas"
    DATA = "data"
    DOCS = "docs"
    LOCAL = "local"
    LOCALISATION = "localisation"


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


class ExcludedWarbands:
    """Warbands to exclude from specific exports."""
    TTS_EXCLUDED = ["Cities of Sigmar"]


class DataTypes:
    """Data type identifiers."""
    FIGHTERS = "fighters"
    ABILITIES = "abilities"
    FACTIONS = "factions"


class FileExtensions:
    """File extensions."""
    JSON = ".json"
    HTML = ".html"
    CSV = ".csv"
    XLSX = ".xlsx"
    MD = ".md"


class OutputFiles:
    """Standard output file names."""
    FIGHTERS_JSON = "fighters.json"
    ABILITIES_JSON = "abilities.json"
    BATTLETRAITS_JSON = "battletraits.json"
    ABILITIES_BATTLETRAITS_JSON = "abilities_battletraits.json"
    FIGHTERS_TTS_JSON = "fighters_tts.json"
    FIGHTERS_LEGACY_JSON = "fighters_legacy.json"
    FIGHTERS_HTML = "fighters.html"
    FIGHTERS_CSV = "fighters.csv"


# Convenience collections
ALL_GRAND_ALLIANCES = [ga.value for ga in GrandAlliances if ga != GrandAlliances.UNIVERSAL]
ALL_FILE_TYPES = [ft.value for ft in FileTypes]
