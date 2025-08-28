"""
Main orchestrator for Warcry data processing pipeline.

Replaces the monolithic WarbandsJSONDataPayload with a clean, focused architecture.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

import jsonschema

from .abilities import Ability
from .constants import FileExtensions, OutputFiles
from .data_loading import WarbandDataLoader
from .data_processing import WarbandDataProcessor
from .exporters import JSONExporter, TTSExporter, HTMLExporter
from .factions import Factions
from .fighters import Fighters
from .models import DataPayload, PROJECT_DATA, PROJECT_ROOT, load_json_file, LOCALISATION_DATA

logger = logging.getLogger(__name__)


class WarbandDataPipeline(DataPayload):
    """
    Main orchestrator for warband data processing.
    
    Coordinates data loading, processing, validation and export operations
    using focused, single-responsibility components.
    """
    
    def __init__(
        self,
        src: Path = PROJECT_DATA,
        schema: Path = Path(PROJECT_ROOT, 'schemas', 'warband_schema.json'),
        src_format: str = 'json',
        filter_string: str = '*.json'
    ):
        if not src.is_dir():
            raise TypeError(f'src must be a dir: {src}')
        
        # Initialize components
        self.loader = WarbandDataLoader(src, filter_string)
        self.json_exporter = JSONExporter()
        self.tts_exporter = TTSExporter()
        self.html_exporter = HTMLExporter()
        
        # Load and process data
        super().__init__(src, schema, src_format)
        
        # Create typed data objects
        self.fighters = Fighters(self.data['fighters'])
        self.abilities = [Ability(x) for x in self.data['abilities']]
        self.factions = Factions(self.data['factions'])
        
        # Process the data
        self.processor = WarbandDataProcessor(self.fighters, self.abilities, self.factions)
        self.processor.process_all(self.data)

    def __repr__(self):
        return f'WarbandDataPipeline(fighters={len(self.fighters.fighters)}, abilities={len(self.abilities)}, factions={len(self.factions.factions)})'

    def load_data(self) -> Dict[str, List[Any]]:
        """Load all warband data using the data loader."""
        return self.loader.load_all_data()

    def validate_data(self):
        """Validate the loaded data against the schema."""
        schema_data = load_json_file(self.schema)
        jsonschema.validate(self.data, schema_data)
        logger.info("Data validation passed")

    # Export methods - JSON formats
    def export_fighters_json(self, dst: Path) -> None:
        """Export fighters to JSON format."""
        self.validate_data()
        self.json_exporter.export_fighters(self.data['fighters'], dst)

    def export_abilities_json(self, dst: Path, exclude_battletraits: bool = False) -> None:
        """Export abilities to JSON format."""
        self.validate_data()
        self.json_exporter.export_abilities(self.data['abilities'], dst, exclude_battletraits)

    def export_battletraits_json(self, dst: Path) -> None:
        """Export battletraits to JSON format."""
        self.validate_data()
        self.json_exporter.export_battletraits(self.data['abilities'], dst)

    def export_warbands_structure(self, dst: Path) -> None:
        """Export data in warband-organized structure."""
        self.validate_data()
        self.json_exporter.export_warbands_structure(
            self.data['fighters'], 
            self.data['abilities'], 
            self.data['factions'], 
            dst
        )

    def export_legacy_fighters(self, dst_root: Path) -> None:
        """Export fighters in legacy format."""
        self.validate_data()
        self.json_exporter.export_legacy_fighters(self.data['fighters'], dst_root)

    # Export methods - TTS format
    def export_tts_fighters(self, dst: Path) -> None:
        """Export fighters in TTS format."""
        self.validate_data()
        self.tts_exporter.export_fighters(self.fighters, dst)

    # Export methods - HTML/CSV/XLSX formats
    def export_fighters_html(self, dst_root: Path) -> None:
        """Export fighters to HTML format."""
        self.validate_data()
        self.html_exporter.export_fighters_html(self.data['fighters'], dst_root)

    def export_fighters_csv(self, dst_root: Path) -> None:
        """Export fighters to CSV format."""
        self.validate_data()
        self.html_exporter.export_fighters_csv(self.data['fighters'], dst_root)

    def export_fighters_xlsx(self, dst_root: Path) -> None:
        """Export fighters to XLSX format."""
        self.validate_data()
        self.html_exporter.export_fighters_xlsx(self.data['fighters'], dst_root)

    def export_fighters_markdown_table(self, dst_root: Path) -> None:
        """Export fighters to Markdown table format."""
        self.validate_data()
        self.html_exporter.export_fighters_markdown_table(self.data['fighters'], dst_root)

    # Localization support
    def export_localized_data(self, loc_file: Path, dst: Path) -> None:
        """Export localized ability data."""
        self.validate_data()
        localization_data = self.loader.load_localisation(loc_file)
        self.json_exporter.export_localized_data(self.data['abilities'], localization_data, dst)

    # Convenience methods
    def export_all_standard_formats(self, dst_root: Path) -> None:
        """Export data in all standard formats.
        
        This replaces the old write_to_disk method.
        """
        logger.info("Starting export of all standard formats")
        
        # JSON exports
        self.export_fighters_json(Path(dst_root, 'fighters.json'))
        self.export_abilities_json(Path(dst_root, 'abilities.json'), exclude_battletraits=True)
        self.export_battletraits_json(Path(dst_root, 'battletraits.json'))
        self.export_abilities_json(Path(dst_root, 'abilities_battletraits.json'), exclude_battletraits=False)
        
        # TTS export
        self.export_tts_fighters(Path(dst_root, 'fighters_tts.json'))
        
        # Other formats
        self.export_fighters_html(dst_root)
        self.export_fighters_csv(dst_root)
        
        # Warband structure
        self.export_warbands_structure(dst_root)
        
        logger.info("Completed export of all standard formats")

    def export_all_with_localization(self, dst_root: Path) -> None:
        """Export all formats including localized versions."""
        # Standard exports
        self.export_all_standard_formats(dst_root)
        
        # Localized exports
        for loc_file in LOCALISATION_DATA.iterdir():
            if loc_file.is_file() and loc_file.suffix == FileExtensions.JSON:
                lang = loc_file.stem
                self.export_localized_data(loc_file, Path(dst_root, lang, OutputFiles.ABILITIES_JSON))
        
        logger.info("Completed export including localization")
