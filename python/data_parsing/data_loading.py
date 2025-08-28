"""
Data loading module for Warcry data processing.

Handles loading fighters, abilities and factions from JSON files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from .constants import FileTypes, FolderNames, DataTypes
from .models import load_json_file, PROJECT_DATA

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Raised when file processing fails."""
    pass


class WarbandDataLoader:
    """Handles loading of warband data from JSON files."""
    
    def __init__(self, src: Path = PROJECT_DATA, filter_string: str = '*.json'):
        self.src = src
        self.filter_str = filter_string
        
        if not src.is_dir():
            raise TypeError(f'src must be a dir: {src}')
    
    def load_all_data(self) -> Dict[str, List[Any]]:
        """Load all warband data from the source directory.
        
        Returns:
            Dictionary containing fighters, abilities and factions lists
        """
        data = {
            DataTypes.FIGHTERS: [],
            DataTypes.ABILITIES: [], 
            DataTypes.FACTIONS: []
        }
        processed_files = 0
        
        for file in self.src.rglob(self.filter_str):
            if not file.is_file():
                logger.debug(f"Skipping non-file: {file}")
                continue
                
            if file.parent.name.lower() == FolderNames.SCHEMAS:
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
        logger.info(f"Total loaded: {len(data[DataTypes.FIGHTERS])} fighters, {len(data[DataTypes.ABILITIES])} abilities, {len(data[DataTypes.FACTIONS])} factions")
        return data
    
    def load_fighters(self) -> List[Dict[str, Any]]:
        """Load only fighter data."""
        data = self.load_all_data()
        return data[DataTypes.FIGHTERS]
    
    def load_abilities(self) -> List[Dict[str, Any]]:
        """Load only ability data."""
        data = self.load_all_data()
        return data[DataTypes.ABILITIES]
    
    def load_factions(self) -> List[Dict[str, Any]]:
        """Load only faction data."""
        data = self.load_all_data()
        return data[DataTypes.FACTIONS]
    
    def load_localisation(self, patch_file: Path) -> List[Dict[str, Any]]:
        """Load localization data from a patch file.
        
        Args:
            patch_file: Path to localization JSON file
            
        Returns:
            List of localized ability data
        """
        try:
            return load_json_file(patch_file)
        except Exception as e:
            logger.error(f"Failed to load localization file {patch_file}: {e}")
            raise FileProcessingError(f"Error loading localization from {patch_file}: {e}") from e
