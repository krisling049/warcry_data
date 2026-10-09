import logging
from html import escape
from pathlib import Path

logger = logging.getLogger(__name__)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Warcry Data</title>
</head>
<body>
<h1>Warcry Data</h1>
<p>Fighter and ability data for Warcry, generated from
<a href="https://github.com/krisling049/warcry_data">github.com/krisling049/warcry_data</a>.</p>
<ul>
{items}
</ul>
</body>
</html>
"""


def export_index(published: list[Path], dst: Path) -> None:
    """Write index.html at dst with a link to each published file, given relative to dst."""
    paths = sorted(p.as_posix() for p in published)
    items = '\n'.join(f'<li><a href="{escape(p)}">{escape(p)}</a></li>' for p in paths)
    index = dst / 'index.html'
    logger.info(f'Exporting index of {len(paths)} files to {index}')
    index.write_text(PAGE.format(items=items), encoding='utf-8', newline='\n')
