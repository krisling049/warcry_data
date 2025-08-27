"""
JSON export functionality for Warcry data.
"""

import logging
from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Any

from ..fighters import sort_fighters, FighterJSONDataPayload
from ..models import write_data_json, sanitise_filename

logger = logging.getLogger(__name__)


class JSONExporter:
    """Handles JSON export operations for warband data."""
    
    def export_fighters(self, fighters_data: List[Dict[str, Any]], dst: Path) -> None:
        """Export fighters to JSON file.
        
        Args:
            fighters_data: List of fighter dictionaries
            dst: Destination file path
        """
        logger.info(f"Exporting {len(fighters_data)} fighters to {dst}")
        sorted_data = sort_fighters([dict(sorted(fighter.items())) for fighter in fighters_data])
        write_data_json(dst=dst, data=sorted_data)
        
    def export_abilities(self, abilities_data: List[Dict[str, Any]], dst: Path, 
                        exclude_battletraits: bool = False) -> None:
        """Export abilities to JSON file.
        
        Args:
            abilities_data: List of ability dictionaries
            dst: Destination file path  
            exclude_battletraits: Whether to exclude battletrait abilities
        """
        data = deepcopy(abilities_data)
        if exclude_battletraits:
            data = [ability for ability in data if ability.get('cost') != 'battletrait']
        
        sorted_data = sorted(data, key=lambda d: d.get('warband', ''))
        logger.info(f"Exporting {len(sorted_data)} abilities to {dst}")
        write_data_json(dst=dst, data=sorted_data)

    def export_battletraits(self, abilities_data: List[Dict[str, Any]], dst: Path) -> None:
        """Export only battletrait abilities to JSON file.
        
        Args:
            abilities_data: List of ability dictionaries
            dst: Destination file path
        """
        battletraits = [ability for ability in abilities_data if ability.get('cost') == 'battletrait']
        sorted_data = sorted(battletraits, key=lambda d: d.get('warband', ''))
        logger.info(f"Exporting {len(sorted_data)} battletraits to {dst}")
        write_data_json(dst=dst, data=sorted_data)
        
    def export_warbands_structure(self, fighters_data: List[Dict[str, Any]], 
                                 abilities_data: List[Dict[str, Any]], 
                                 factions_data: List[Dict[str, Any]], 
                                 dst: Path) -> None:
        """Export data in warband-organized structure.
        
        Args:
            fighters_data: List of fighter dictionaries
            abilities_data: List of ability dictionaries 
            factions_data: List of faction dictionaries
            dst: Base destination directory
        """
        logger.info("Exporting warband-organized structure")
        
        data_structure = {'universal': {'faction': {}, 'fighters': [], 'abilities': []}}
        faction_mapping = {'universal': 'universal'}

        # Build faction mapping
        for faction in factions_data:
            warband = faction.get('warband')
            if warband and warband not in data_structure:
                data_structure[warband] = {'faction': faction, 'fighters': [], 'abilities': []}
            faction_mapping[warband] = warband
            
            # Handle subfactions/bladeborn
            for subfaction in faction.get('subfactions', []):
                if subfaction.get('bladeborn'):
                    faction_mapping[subfaction.get('runemark')] = warband

        # Organize fighters by warband
        for fighter in fighters_data:
            warband = fighter.get('warband')
            if warband in data_structure:
                data_structure[warband]['fighters'].append(fighter)

        # Organize abilities by warband
        for ability in abilities_data:
            ability_warband = ability.get('warband')
            mapped_warband = faction_mapping.get(ability_warband, ability_warband)
            if mapped_warband in data_structure:
                data_structure[mapped_warband]['abilities'].append(ability)

        # Write files
        for warband, warband_data in data_structure.items():
            for datatype, content in warband_data.items():
                grand_alliance = 'universal' if warband == 'universal' else warband_data['faction'].get('grand_alliance')
                faction_runemark = 'universal' if warband == 'universal' else warband_data['faction'].get('warband')

                if faction_runemark == 'universal' and datatype != 'abilities':
                    continue

                filename = f'{faction_runemark}_{datatype}.json'
                path_parts = [
                    p for p in [
                        dst,
                        grand_alliance,
                        sanitise_filename(faction_runemark) if warband != 'universal' else '',
                        sanitise_filename(filename)
                    ] if p
                ]
                outfile = Path(*path_parts)

                if isinstance(content, list):
                    logger.info(f'{warband} - writing {len(content)} items to {outfile}')
                else:
                    logger.info(f'{warband} - writing {outfile}')

                write_data_json(dst=outfile, data=content)
                
    def export_legacy_fighters(self, fighters_data: List[Dict[str, Any]], dst_root: Path) -> None:
        """Export fighters in legacy format.
        
        Args:
            fighters_data: List of fighter dictionaries
            dst_root: Root destination directory
        """
        logger.info("Exporting fighters in legacy format")
        FighterJSONDataPayload(preloaded_data=fighters_data).write_legacy_format(dst_root=dst_root)
        
    def export_localized_data(self, abilities_data: List[Dict[str, Any]], 
                             localization_data: Dict[str, Any], dst: Path) -> None:
        """Export localized ability data.
        
        Args:
            abilities_data: List of ability dictionaries
            localization_data: Localization mapping dictionary
            dst: Destination file path
        """
        temp_data = deepcopy(abilities_data)
        
        for ability in temp_data:
            ability_id = ability.get('_id')
            if ability_id in localization_data:
                ability.update(localization_data[ability_id])
            else:
                logger.warning(f"Localization not found for {ability_id} - {ability.get('name')}")
        
        sorted_data = sorted(temp_data, key=lambda d: d.get('warband', ''))
        logger.info(f"Exporting {len(sorted_data)} localized abilities to {dst}")
        write_data_json(dst=dst, data=sorted_data)
