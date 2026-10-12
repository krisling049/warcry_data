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
| `python python/data_server.py [--data PATH] [--port 4424]` | Serve the editor at `http://127.0.0.1:4424/`. Create, edit and delete warbands, factions, fighters and abilities. |
| `python -m pytest` | Run the tests. |

## Editor

The editor is a web page in `web/`, served by `data_server.py`. It reads and writes files through
`data_parsing/data_store.py`. Select an item in the tree on the left, then edit it in the form on the right.

- **Save** (Ctrl+S) checks the item against its schema, then writes its file. A save keeps unknown keys, key order and line endings.
- **New fighter** and **New ability** add to the selected warband. New items get a unique `_id`.
- **Duplicate** saves a copy of the selected fighter or ability with a new `_id`.
- **New warband** makes a folder with empty fighters and abilities files and a faction file.
- **Delete warband** deletes the folder and all its files.
- **Validate all** runs the same checks as `validation.py`.

The editor cannot rename a warband or a subfaction, or remove a subfaction that a fighter or ability uses. Edit the
JSON files to do that.

A save writes the whole file in the standard format (4-space indent), so a file with other spacing changes on its
first save. Use one tab per data folder: the last save wins, and a save from a stale tab adds back an item that
was deleted in another tab.

The filter box matches a grand alliance, warband, subfaction, fighter or ability name. The URL of each item
(`#<warband folder>/<type>/<_id>`) opens that item. The server listens on 127.0.0.1 only. It refuses requests with an unknown `Host` header, and changes that
are not sent as `application/json`, so other web pages cannot change your data.

## Pipeline

- `data_loading.py` - loads every `*_fighters.json`, `*_abilities.json` and `*_faction.json` in sorted path order.
- `schema_validation.py` - validates each entity against `schemas/` and checks that `_id`s are unique.
- `data_processing.py` - finds each fighter's subfaction and assigns abilities by warband, subfaction and runemarks.
- `warband_pipeline.py` - runs the steps above and writes all outputs.
- `exporters/` - JSON, Tabletop Simulator, HTML and CSV writers.

## Outputs

`abilities.json`, `battletraits.json`, `abilities_battletraits.json`, `fighters.json`, `fighters_tts.json`,
`fighters.html`, `fighters.csv`, `<language>/abilities.json` for each file in `localisation/`, and `index.html`,
which links to each of the other files.

A localisation file maps an ability `_id` to its translated fields. Leave an ability out until it is translated;
the export then uses the English text.
