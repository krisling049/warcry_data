# Warcry Data

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://krisling049.github.io/warcry_data/)
[![Data Validation](https://img.shields.io/badge/Data-Validated-blue)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()

A consolidated home for data used by Warcry tools

## Table of Contents
- [Overview](#overview)
- [Data Access](#data-access)
- [Development](#development)
- [Data Structure](#data-structure)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [Disclaimer](#disclaimer)

## Overview

This repository contains comprehensive JSON data covering all fighters and abilities in Warcry. The data is structured for programmatic access and used by various Warcry tools and applications.

### Key Features
- ✅ **Complete Data Coverage**: All Matched Play fighters, abilities and factions
- ✅ **Validated Structure**: JSON schema validation ensures data integrity  
- ✅ **Multiple Formats**: JSON, HTML, CSV, TTS-compatible exports
- ✅ **Programmatic Access**: Python tools for data manipulation
- ✅ **Live Updates**: Published via GitHub Pages

## Data Access

### Programmatic Access
Retrieve data directly from our GitHub Pages deployment:

```bash
# All fighters data
curl https://krisling049.github.io/warcry_data/fighters.json

# All abilities data  
curl https://krisling049.github.io/warcry_data/abilities.json

# Tabletop Simulator format
curl https://krisling049.github.io/warcry_data/fighters_tts.json
```

### Available Endpoints
| Endpoint | Description | Format |
|----------|-------------|---------|
| `/fighters.json` | Complete fighter data | JSON |
| `/abilities.json` | Abilities (excluding battletraits) | JSON |
| `/abilities_battletraits.json` | All abilities including battletraits | JSON |
| `/fighters_tts.json` | Tabletop Simulator format | JSON |
| `/fighters.html` | Human-readable fighter table | HTML |
| `/fighters.csv` | Fighter data for spreadsheets | CSV |

## Development

### Python Tools
The repository includes Python tools for data manipulation:

```bash
# Install dependencies
pip install -r python/requirements.txt

# Validate all data
python python/validation.py

# Export data formats
# Use -local to avoid contaminating published data
python python/export_data.py -local
```

### Data Structure
```
data/
├── chaos/           # Chaos Grand Alliance
├── death/           # Death Grand Alliance  
├── destruction/     # Destruction Grand Alliance
├── order/           # Order Grand Alliance
└── universal/       # Universal abilities

Each warband contains:
├── {warband}_fighters.json    # Fighter statistics
├── {warband}_abilities.json   # Warband abilities
└── {warband}_faction.json     # Faction metadata
```

## Contributing

1. **Source of Truth**: Files in `data/` are authoritative
2. **Generated Files**: `docs/` content is auto-generated - don't edit manually
3. **Validation**: All changes must pass schema validation
4. **Testing**: Run validation before submitting PRs

```bash
# Validate your changes
python python/validation.py
```

## Acknowledgements

Special thanks to these valuable contributors:

| Contributor | Projects | Links |
|-------------|----------|-------|
| **Baz** | Optimal Game State, Warcry Card Creator | [YouTube](https://www.youtube.com/@optimalgamestate) • [Card Creator](https://barrysheppard.github.io/warcry-card-creator/) • [GitHub](https://github.com/barrysheppard) |
| **Servo-Scribe** | Warcrier, Necrodamus, Mordheimer | [Warcrier](https://warcrier.net/) • [Necrodamus](https://necrodamus.org/) • [Mordheimer](https://mordheimer.net/) |
| **Hood** | Warcry Tabletop Simulator | [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3328937378) |

## Disclaimer

> **⚠️ Unofficial Fan Project**
> 
> This is an entirely unofficial fan project and is in no way associated with Games Workshop or any other company. It is a non-commercial and non-profit project developed out of love for Warcry as a game and setting.
>
> **No commercial use** • **No money requested or received** • **Personal time contribution only**
>
> For legal communication or takedown requests, please [get in touch](https://github.com/krisling049).

---

**Made with ❤️ by the Warcry community**
