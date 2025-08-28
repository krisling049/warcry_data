# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**Source Data:** `data/` - The source of truth
**Generated Data:** `docs/` - This is published via GitHub Pages.

## Development Commands

### Data Validation
```bash
# Install dependencies
pip install -r python/requirements.txt

# Validate all data against JSON schemas
python python/validation.py

# Validate specific data folder (optional)
python python/validation.py --data /path/to/data
```

### Data Export and Generation
```bash
# Export data to docs/ (for GitHub Pages publishing)
python python/export_data.py

# Export data to local untracked folder for testing
python python/export_data.py -local
```

## Architecture Overview

### Data Structure
- **Source Data**: Located in `data/{grand_alliance}/{warband}/` with three JSON files per warband:
  - `{warband}_fighters.json` - Fighter statistics and weapons
  - `{warband}_abilities.json` - Warband-specific abilities 
  - `{warband}_faction.json` - Faction metadata and battletraits
- **Universal Data**: `data/universal/universal_abilities.json` contains abilities shared across warbands
- **Schemas**: `schemas/` contains JSON schemas for validation of fighters, abilities, factions and aggregated data

### Core Data Processing
- **models.py**: Base classes `DataPayload` and `JSONDataPayload` for loading, validating and writing JSON data
- **warband_pipeline.py**: Main orchestrator `WarbandDataPipeline` coordinates data loading, processing and export operations
- **data_loading.py**: `WarbandDataLoader` handles all file loading operations across Grand Alliances
- **data_processing.py**: `WarbandDataProcessor` handles ID, ability and faction assignment
- **Export Modules**:
  - `exporters/json_exporter.py` - `JSONExporter` for JSON formats
  - `exporters/tts_exporter.py` - `TTSExporter` for Tabletop Simulator format  
  - `exporters/html_exporter.py` - `HTMLExporter` for HTML/CSV/XLSX/Markdown
- **Data Type Modules**: 
  - `fighters.py`, `abilities.py`, `factions.py` - Handle specific data types with schema validation
  - Each module defines schema paths and data structures with type annotations

### Exported Formats
The export process generates multiple output formats in `docs/`:
- `fighters.json` - All fighters aggregated
- `abilities.json` - All abilities (excluding battletraits)
- `battletraits.json` - Faction battletraits only
- `abilities_battletraits.json` - All abilities including battletraits
- `fighters_tts.json` - Tabletop Simulator format
- `fighters.html` - HTML table for web viewing
- `fighters.csv` - CSV export
- Localized data in language subdirectories (e.g., `french/abilities.json`)

### Validation System
All data is validated against JSON schemas before export. The validation system:
- **Schema Validation**: Uses `validation_system.py` with structured result objects and detailed error reporting
- **Business Rules**: Uses `business_rules.py` for configurable validation rules (points limits, movement ranges, etc.)
- **Schema Files**: Validates against `fighter_schema.json`, `ability_schema.json`, `faction_schema.json`
- **Comprehensive Reporting**: Provides detailed validation results with error paths and context
- Runs automatically via GitHub Actions on data changes

### Supporting Systems
- **Business Rules**: `business_rules.py` contains configurable rules for TTS export exclusions and validation logic
- **Logging**: `logging_config.py` provides structured logging with performance monitoring and multiple output formats
- **Constants**: `constants.py` centralizes all magic strings, file paths and configuration values

### Key File Locations
- Source data: `data/{chaos|death|destruction|order}/{warband}/`
- Schemas: `schemas/{fighter|ability|faction}_schema.json`
- Python processing: `python/data_parsing/`
- Generated outputs: `docs/`
- Localization: `localisation/`

## Token-Efficient Search Commands

Use these commands to efficiently query the JSON data without reading entire files. These use grep, find, and basic shell commands available in most environments.

### Fighter Data Queries
```bash
# Get all fighter names from a specific grand alliance
find data/chaos -name "*_fighters.json" -exec grep -h '"name":' {} + | cut -d'"' -f4

# Find fighters with high movement (6+)
find data -name "*_fighters.json" -exec grep -A1 -B1 '"movement": [6-9]' {} +

# Count fighters per grand alliance
for ga in chaos death destruction order; do echo "$ga: $(find data/$ga -name "*_fighters.json" -exec grep -c '"name":' {} \; | paste -sd+ | bc)"; done

# Find fighters by warband
find data -name "*_fighters.json" -exec grep -l "Stormcast" {} +

# Get weapon types used
find data -name "*_fighters.json" -exec grep -h '"runemark":' {} + | sort | uniq -c | sort -nr
```

### Ability Data Queries  
```bash
# Find abilities by name pattern (case insensitive)
find data -name "*_abilities.json" -exec grep -i '"name":.*strike' {} +

# Get abilities with specific costs
find data -name "*_abilities.json" -exec grep -h '"cost": "double"' {} +

# Find abilities by warband
find data -name "*_abilities.json" -exec grep -A5 -B5 '"warband": "Stormcast"' {} +

# Count abilities per cost type
for cost in double triple quad reaction battletrait; do echo "$cost: $(find data -name "*_abilities.json" -exec grep -c "\"cost\": \"$cost\"" {} \; | paste -sd+ | bc)"; done
```

### Faction/Warband Queries
```bash
# List all warbands in a grand alliance
ls data/chaos/ | grep -v ".json"

# Find factions with battletraits
grep -l '"battletrait"' data/*/*/*_abilities.json

# Get warband names 
find data -name "*_fighters.json" -exec grep -h '"warband":' {} \; | sort | uniq -c
```

### Validation and Data Quality Queries
```bash
# Find fighters missing movement/toughness/wounds
grep -L '"movement":\|"toughness":\|"wounds":' data/*/*/*_fighters.json

# Find duplicate IDs across all fighters  
find data -name "*_fighters.json" -exec grep -h '"_id":' {} \; | sort | uniq -d

# Get weapon runemark distribution
find data -name "*_fighters.json" -exec grep -h '"runemark":' {} \; | sort | uniq -c | sort -nr

# Check warband name consistency
find data -name "*_fighters.json" -exec grep -h '"warband":' {} \; | sort | uniq -c
```

### Quick Existence Checks
```bash
# Check if a specific fighter exists
grep -r "Bloodstoker" data/*/*/*_fighters.json

# Count total fighters and abilities
echo "Fighters: $(find data -name "*_fighters.json" -exec grep -c '"name":' {} \; | paste -sd+ | bc)"
echo "Abilities: $(find data -name "*_abilities.json" -exec grep -c '"name":' {} \; | paste -sd+ | bc)"
```

### File-Specific Searches (Most Token-Efficient)
```bash
# Search within specific warband files when warband is known
grep '"name":.*Lord' data/chaos/slaves_to_darkness/slaves_to_darkness_fighters.json

# Get all abilities for a specific warband
grep -A2 '"name":' data/order/stormcast_eternals_warrior_chamber/stormcast_eternals_warrior_chamber_abilities.json
```

## Data Rules
- Fighters and Abilities require unique `_id` fields (generated from UUID4 beginning)
- Grand alliances must be one of: chaos, death, destruction, order
- All weapon and ability references must be consistent across related files
- Schema validation is enforced - data export will fail if validation errors exist
