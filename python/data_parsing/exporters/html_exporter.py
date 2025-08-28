"""
HTML and other format export functionality for Warcry data.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from ..fighters import FighterJSONDataPayload

logger = logging.getLogger(__name__)


class HTMLExporter:
    """Handles HTML, CSV, XLSX and Markdown export operations."""
    
    def export_fighters_html(self, fighters_data: List[Dict[str, Any]], dst_root: Path) -> None:
        """Export fighters to HTML format.
        
        Args:
            fighters_data: List of fighter dictionaries
            dst_root: Root destination directory
        """
        logger.info(f"Exporting {len(fighters_data)} fighters to HTML format")
        FighterJSONDataPayload(preloaded_data=fighters_data).write_html(dst_root=dst_root)
        
    def export_fighters_csv(self, fighters_data: List[Dict[str, Any]], dst_root: Path) -> None:
        """Export fighters to CSV format.
        
        Args:
            fighters_data: List of fighter dictionaries
            dst_root: Root destination directory
        """
        logger.info(f"Exporting {len(fighters_data)} fighters to CSV format")
        FighterJSONDataPayload(preloaded_data=fighters_data).write_csv(dst_root=dst_root)
        
    def export_fighters_xlsx(self, fighters_data: List[Dict[str, Any]], dst_root: Path) -> None:
        """Export fighters to XLSX format.
        
        Args:
            fighters_data: List of fighter dictionaries
            dst_root: Root destination directory
        """
        logger.info(f"Exporting {len(fighters_data)} fighters to XLSX format")
        FighterJSONDataPayload(preloaded_data=fighters_data).write_xlsx(dst_root=dst_root)
        
    def export_fighters_markdown_table(self, fighters_data: List[Dict[str, Any]], dst_root: Path) -> None:
        """Export fighters to Markdown table format.
        
        Args:
            fighters_data: List of fighter dictionaries
            dst_root: Root destination directory
        """
        logger.info(f"Exporting {len(fighters_data)} fighters to Markdown table format")
        FighterJSONDataPayload(preloaded_data=fighters_data).write_markdown_table(dst_root=dst_root)
