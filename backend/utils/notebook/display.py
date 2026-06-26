"""Theme-aware notebook display helpers (VS Code / Jupyter dark theme)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEBUG_LOG = _REPO_ROOT / "debug-bd36d7.log"
_DEBUG_SESSION = "bd36d7"


def _bg_snippets(html: str) -> list[str]:
    return [m.group(0)[:80] for m in re.finditer(r"background[^;\"']{0,80}", html, re.I)]


# region agent log
def _debug_theme_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": _DEBUG_SESSION,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with _DEBUG_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


# endregion


def notebook_html_transparent(html: str) -> str:
    """Strip hard-coded light backgrounds from Rich/HTML fragments."""
    # region agent log
    before = _bg_snippets(html)
    # endregion
    cleaned = re.sub(
        r"background-color:\s*#ffffff\b",
        "background-color: transparent",
        html,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"background-color:\s*white\b",
        "background-color: transparent",
        cleaned,
        flags=re.IGNORECASE,
    )
    # region agent log
    _debug_theme_log(
        "A",
        "display.py:notebook_html_transparent",
        "rich/html background cleanup",
        {"before": before, "after": _bg_snippets(cleaned)},
    )
    # endregion
    return cleaned


_NOTEBOOK_DF_CSS = """
<style>
.nb-theme-df, .nb-theme-df table.dataframe {
    background: transparent !important;
    color: inherit !important;
}
.nb-theme-df th, .nb-theme-df td {
    background: transparent !important;
    color: inherit !important;
}
</style>
"""

_NOTEBOOK_RICH_CSS = """
<style>
.nb-theme-rich pre,
.nb-theme-rich code {
    background: transparent !important;
    color: inherit !important;
}
.nb-theme-rich span.r3 {
    color: inherit !important;
}
</style>
"""


def wrap_notebook_rich_html(html: str) -> str:
    """Make Rich-exported HTML readable on dark notebook themes."""
    cleaned = notebook_html_transparent(html)
    cleaned = re.sub(
        r"color:\s*#000000\b",
        "color: inherit",
        cleaned,
        flags=re.IGNORECASE,
    )
    style_match = re.search(r"<style>.*?</style>", cleaned, re.DOTALL | re.IGNORECASE)
    body_match = re.search(r"<body[^>]*>(.*)</body>", cleaned, re.DOTALL | re.IGNORECASE)
    if body_match is None:
        return f'{_NOTEBOOK_RICH_CSS}<div class="nb-theme-rich">{cleaned}</div>'
    style = style_match.group(0) if style_match else ""
    content = body_match.group(1)
    return f'{_NOTEBOOK_RICH_CSS}{style}<div class="nb-theme-rich">{content}</div>'


def display_notebook_dataframe(df: "pd.DataFrame") -> None:
    """Display a pandas table without forcing a light HTML background."""
    from IPython.display import HTML, display

    raw = df._repr_html_() or df.to_html(classes="dataframe", border=0)
    wrapped = f'{_NOTEBOOK_DF_CSS}<div class="nb-theme-df">{raw}</div>'
    # region agent log
    _debug_theme_log(
        "B,E",
        "display.py:display_notebook_dataframe",
        "display dataframe",
        {
            "rows": len(df),
            "raw_bg": _bg_snippets(raw),
            "wrapped_bg": _bg_snippets(wrapped),
        },
    )
    # endregion
    display(HTML(wrapped))
