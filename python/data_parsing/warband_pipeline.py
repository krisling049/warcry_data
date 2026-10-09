import logging
from pathlib import Path

from .abilities import Ability
from .constants import ABILITIES, FACTIONS, FIGHTERS
from .data_loading import load_all_data
from .data_processing import assign_abilities, assign_subfactions
from .exporters import html_exporter, index_exporter, json_exporter, tts_exporter
from .fighters import Fighter
from .models import LOCALISATION_DATA, PROJECT_DATA, load_json_file
from .schema_validation import validate_data

logger = logging.getLogger(__name__)


class WarbandDataPipeline:
    """Loads and validates all warband data, then links fighters to their abilities."""

    def __init__(self, src: Path = PROJECT_DATA):
        self.data = load_all_data(src)
        errors = validate_data(self.data)
        if errors:
            raise ValueError(f'{len(errors)} validation errors:\n' + '\n'.join(errors))

        self.abilities = [Ability(a) for a in self.data[ABILITIES]]
        self.fighters = [Fighter(f) for f in self.data[FIGHTERS]]
        assign_subfactions(self.fighters, self.data[FACTIONS])
        assign_abilities(self.fighters, self.abilities)

    def export_all(self, dst: Path, localisation: Path = LOCALISATION_DATA) -> None:
        abilities = self.data[ABILITIES]
        fighters = self.data[FIGHTERS]
        published: list[Path] = []

        def out(*parts: str) -> Path:
            published.append(Path(*parts))
            return dst.joinpath(*parts)

        json_exporter.export_abilities(abilities, out('abilities.json'), exclude_battletraits=True)
        json_exporter.export_battletraits(abilities, out('battletraits.json'))
        json_exporter.export_abilities(abilities, out('abilities_battletraits.json'), exclude_battletraits=False)
        json_exporter.export_fighters(fighters, out('fighters.json'))
        tts_exporter.export_fighters(self.fighters, out('fighters_tts.json'))
        html_exporter.export_fighters_html(fighters, out('fighters.html'))
        html_exporter.export_fighters_csv(fighters, out('fighters.csv'))
        for loc_file in sorted(localisation.glob('*.json')):
            translations = load_json_file(loc_file, dict)
            json_exporter.export_localized_abilities(abilities, translations, out(loc_file.stem, 'abilities.json'))
        index_exporter.export_index(published, dst)
