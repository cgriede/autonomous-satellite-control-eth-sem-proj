"""Theme-aware notebook display helpers (VS Code / Jupyter dark theme)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

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


def notebook_html_transparent(html: str) -> str:
    """Strip hard-coded light backgrounds from Rich/HTML fragments."""
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
    return cleaned


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
    display(HTML(wrapped))
