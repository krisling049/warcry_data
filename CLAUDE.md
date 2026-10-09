# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**Source Data:** `data/` - The source of truth
**Generated Data:** `docs/` - Built by `python/export_data.py`. Git ignores it. CI deploys it to GitHub Pages
(https://krisling049.github.io/warcry_data/). The file names in it are a public contract: third-party tools fetch them by URL.

## Development Commands
```bash
pip install -r python/requirements.txt

# Report every validation error (optionally for another data folder)
python python/validation.py [--data /path/to/data]

# Validate, then write all published files (default out: docs/)
python python/export_data.py [--data PATH] [--out PATH]

# Tests
python -m pytest
```

## Architecture Overview

### Data Structure
- **Source Data**: `data/{grand_alliance}/{warband}/` with three JSON files per warband:
  - `{warband}_fighters.json` - Fighter statistics and weapons
  - `{warband}_abilities.json` - Warband and subfaction abilities
  - `{warband}_faction.json` - Faction metadata and subfactions
- **Universal Data**: `data/universal/universal_abilities.json` contains abilities shared across warbands
- **Schemas**: `schemas/{fighter|ability|faction}_schema.json`, one per entity type
- **Localisation**: `localisation/{language}.json` maps ability `_id` to translated fields

### Python (`python/data_parsing/`)
- `data_loading.py` - `load_all_data` loads all source files in sorted path order
- `schema_validation.py` - `validate_data` returns every schema error and duplicate `_id`
- `data_processing.py` - assigns subfactions, then abilities, to fighters
- `warband_pipeline.py` - `WarbandDataPipeline` loads, validates (raises on any error), processes and exports
- `exporters/` - `json_exporter`, `tts_exporter`, `html_exporter` (HTML and CSV through pandas)

### Exported Formats (`docs/`)
- `fighters.json` - All fighters
- `abilities.json` - All abilities except battletraits
- `battletraits.json` - Battletraits only
- `abilities_battletraits.json` - All abilities including battletraits
- `fighters_tts.json` - Tabletop Simulator format
- `fighters.html`, `fighters.csv` - Fighter tables
- `{language}/abilities.json` - Localised abilities

### CI
`.github/workflows/pages.yml` runs the tests and the export on every PR. On `main` it also deploys `docs/` to GitHub Pages.

## Searching the Data
```bash
# Find a fighter or ability by name
grep -rn '"name": "Bloodstoker"' data/

# All fighters of a warband
jq -r '.[].name' data/order/twistweald/twistweald_fighters.json

# Fighters with movement 6 or more, across all warbands
jq -r '.[] | select(.movement >= 6) | "\(.warband): \(.name)"' data/*/*/*_fighters.json

# Abilities of one cost type
jq -r '.[] | select(.cost == "reaction") | "\(.warband): \(.name)"' data/*/*/*_abilities.json
```

## Data Rules
- Fighters and Abilities require a unique `_id` of 8 lowercase letters or digits (e.g. the start of a uuid4)
- Grand alliances must be one of: chaos, death, destruction, order
- All weapon and ability references must be consistent across related files
- Schema validation is enforced - the export fails if any validation error exists
- A localisation entry holds only translated text; leave an ability out until it is translated
