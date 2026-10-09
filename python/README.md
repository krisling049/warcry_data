# Warcry Data Python Tools

Validates the source data in `data/` and builds the published files.

## Setup

Python 3.10 or later.

```bash
python -m venv .venv
.venv/Scripts/pip install -r python/requirements.txt   # Windows
.venv/bin/pip install -r python/requirements.txt       # macOS/Linux
```

Run all commands from the repository root.

## Scripts

| Command | Purpose |
|---------|---------|
| `python python/validation.py [--data PATH]` | Report every schema error and duplicate `_id`. Exits 1 if any exist. |
| `python python/export_data.py [--data PATH] [--out PATH]` | Validate, then write all published files (default `docs/`, which git ignores). |
| `python -m pytest` | Run the tests. |

## Pipeline

- `data_loading.py` - loads every `*_fighters.json`, `*_abilities.json` and `*_faction.json` in sorted path order.
- `schema_validation.py` - validates each entity against `schemas/` and checks that `_id`s are unique.
- `data_processing.py` - finds each fighter's subfaction and assigns abilities by warband, subfaction and runemarks.
- `warband_pipeline.py` - runs the steps above and writes all outputs.
- `exporters/` - JSON, Tabletop Simulator, HTML and CSV writers.

## Outputs

`abilities.json`, `battletraits.json`, `abilities_battletraits.json`, `fighters.json`, `fighters_tts.json`,
`fighters.html`, `fighters.csv`, and `<language>/abilities.json` for each file in `localisation/`.

A localisation file maps an ability `_id` to its translated fields. Leave an ability out until it is translated;
the export then uses the English text.
