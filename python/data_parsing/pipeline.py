"""
Warcry data processing pipeline.

Orchestrates loading, processing and exporting of warband data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from .config import FileTypes, DataTypes, PROJECT_DATA, LOCALISATION_DATA
from .io import load_json_file, validate_against_schema
from .models import Ability, Faction, Fighter, WarbandData
from .processing import assign_ids, assign_abilities, assign_factions

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Raised when file processing fails."""
    pass


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_warband_data(src: Path = PROJECT_DATA,
                      schema: Path = None,
                      filter_string: str = '*.json') -> Dict[str, List[Any]]:
    """Load all warband data from source directory and validate.

    Args:
        src: Source directory containing warband data files
        schema: Optional schema to validate against
        filter_string: Glob pattern for files to load

    Returns:
        Dictionary containing 'fighters', 'abilities' and 'factions' lists

    Raises:
        TypeError: If src is not a directory
        FileProcessingError: If file loading fails
    """
    if not src.is_dir():
        raise TypeError(f'src must be a dir: {src}')

    data = {
        DataTypes.FIGHTERS: [],
        DataTypes.ABILITIES: [],
        DataTypes.FACTIONS: []
    }
    processed_files = 0

    for file in src.rglob(filter_string):
        if not file.is_file():
            logger.debug(f"Skipping non-file: {file}")
            continue

        if file.parent.name.lower() == "schemas":
            logger.debug(f"Skipping schema file: {file}")
            continue

        try:
            if file.name.endswith(FileTypes.FIGHTERS.value):
                content = load_json_file(file)
                data[DataTypes.FIGHTERS].extend(content)
                processed_files += 1
                logger.info(f"Loaded {len(content)} fighters from {file}")

            elif file.name.endswith(FileTypes.ABILITIES.value):
                content = load_json_file(file)
                data[DataTypes.ABILITIES].extend(content)
                processed_files += 1
                logger.info(f"Loaded {len(content)} abilities from {file}")

            elif file.name.endswith(FileTypes.FACTION.value):
                content = load_json_file(file)
                data[DataTypes.FACTIONS].append(content)
                processed_files += 1
                logger.info(f"Loaded faction data from {file}")

        except Exception as e:
            logger.error(f"Failed to process file {file}: {e}")
            raise FileProcessingError(f"Error processing {file}: {e}") from e

    logger.info(f"Successfully processed {processed_files} data files")
    logger.info(f"Total loaded: {len(data[DataTypes.FIGHTERS])} fighters, "
                f"{len(data[DataTypes.ABILITIES])} abilities, "
                f"{len(data[DataTypes.FACTIONS])} factions")

    # Validate if schema provided
    if schema:
        validate_against_schema(data, schema)
        logger.info("Data validation passed")

    return data


def load_localisation(patch_file: Path) -> List[Dict[str, Any]]:
    """Load localization data from a patch file.

    Args:
        patch_file: Path to localization JSON file

    Returns:
        List of localized ability data

    Raises:
        FileProcessingError: If loading fails
    """
    try:
        return load_json_file(patch_file)
    except Exception as e:
        logger.error(f"Failed to load localization file {patch_file}: {e}")
        raise FileProcessingError(f"Error loading localization from {patch_file}: {e}") from e


# ============================================================================
# DATA PROCESSING
# ============================================================================

def process_warband_data(data: Dict[str, List[Dict[str, Any]]]) -> WarbandData:
    """Process warband data by converting to typed objects and making assignments.

    Args:
        data: Dictionary containing 'fighters', 'abilities', 'factions' as lists of dicts

    Returns:
        WarbandData container with typed, enriched objects
    """
    logger.info("Starting data processing pipeline")

    # Step 1: Assign IDs to raw data
    assign_ids(data)

    # Step 2: Convert to typed objects
    fighters = [Fighter.from_dict(x) for x in data[DataTypes.FIGHTERS]]
    abilities = [Ability.from_dict(x) for x in data[DataTypes.ABILITIES]]
    factions = [Faction.from_dict(f) for f in data[DataTypes.FACTIONS]]

    # Step 3: Assign factions (must come before abilities)
    assign_factions(fighters, factions)

    # Step 4: Assign abilities
    assign_abilities(fighters, abilities)

    logger.info("Data processing pipeline completed")

    return WarbandData(fighters=fighters, abilities=abilities, factions=factions)


# ============================================================================
# EXPORT ORCHESTRATION FUNCTIONS
# ============================================================================

def export_all_formats(warband_data: WarbandData, raw_data: Dict[str, List[Dict]], dst_root: Path) -> None:
    """Export data in all standard formats.

    Args:
        warband_data: Typed WarbandData with enriched Fighter objects
        raw_data: Raw dict data for JSON/tabular exports that need source format
        dst_root: Root directory for output files
    """
    from .exporters import json_exporter, tts_exporter, tabular_exporter

    logger.info("Starting export of all standard formats")

    # JSON exports (use raw dicts for backward-compatible output)
    json_exporter.export_fighters(raw_data[DataTypes.FIGHTERS], Path(dst_root, 'fighters.json'))
    json_exporter.export_abilities(raw_data[DataTypes.ABILITIES], Path(dst_root, 'abilities.json'), exclude_battletraits=True)
    json_exporter.export_battletraits(raw_data[DataTypes.ABILITIES], Path(dst_root, 'battletraits.json'))
    json_exporter.export_abilities(raw_data[DataTypes.ABILITIES], Path(dst_root, 'abilities_battletraits.json'), exclude_battletraits=False)

    # TTS export (uses typed fighters with abilities already assigned)
    tts_exporter.export_tts_fighters(warband_data.fighters, Path(dst_root, 'fighters_tts.json'))

    # Tabular formats (HTML, CSV - use raw dicts)
    tabular_exporter.export_fighters_html(raw_data[DataTypes.FIGHTERS], dst_root)
    tabular_exporter.export_fighters_csv(raw_data[DataTypes.FIGHTERS], dst_root)

    # Warband structure (uses raw dicts)
    json_exporter.export_warbands_structure(
        raw_data[DataTypes.FIGHTERS],
        raw_data[DataTypes.ABILITIES],
        raw_data[DataTypes.FACTIONS],
        dst_root
    )

    logger.info("Completed export of all standard formats")


def export_all_with_localization(warband_data: WarbandData, raw_data: Dict[str, List[Dict]], dst_root: Path) -> None:
    """Export all formats including localized versions.

    Args:
        warband_data: Typed WarbandData with enriched Fighter objects
        raw_data: Raw dict data for JSON/tabular exports
        dst_root: Root directory for output files
    """
    from .exporters import json_exporter

    # Standard exports
    export_all_formats(warband_data, raw_data, dst_root)

    # Localized exports
    for loc_file in LOCALISATION_DATA.iterdir():
        if loc_file.is_file() and loc_file.suffix == ".json":
            lang = loc_file.stem
            localization_data = load_localisation(loc_file)
            json_exporter.export_localized_data(
                raw_data[DataTypes.ABILITIES],
                localization_data,
                Path(dst_root, lang, "abilities.json")
            )

    logger.info("Completed export including localization")
