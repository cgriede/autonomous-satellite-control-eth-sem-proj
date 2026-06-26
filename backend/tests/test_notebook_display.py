"""Tests for theme-aware notebook display helpers."""

from utils.notebook.display import (
    display_notebook_dataframe,
    notebook_html_transparent,
    wrap_notebook_rich_html,
)


def test_notebook_html_transparent_strips_white_background() -> None:
    html = '<div style="background-color: #ffffff">x</div>'
    cleaned = notebook_html_transparent(html)
    assert "#ffffff" not in cleaned
    assert "transparent" in cleaned


def test_wrap_notebook_rich_html_uses_inherit_for_black_text() -> None:
    html = """<!DOCTYPE html><html><head><style>
body { color: #000000; background-color: #ffffff; }
</style></head><body><pre><code>value text</code></pre></body></html>"""
    wrapped = wrap_notebook_rich_html(html)
    assert "#000000" not in wrapped
    assert "color: inherit" in wrapped
    assert "nb-theme-rich" in wrapped
    assert "#ffffff" not in wrapped


def test_display_notebook_dataframe_emits_transparent_css(monkeypatch) -> None:
    import pandas as pd

    captured: list = []

    def _fake_display(obj, **_kwargs):
        captured.append(obj)

    monkeypatch.setattr("IPython.display.display", _fake_display)
    display_notebook_dataframe(pd.DataFrame({"a": [1]}))
    assert captured
    html = captured[0].data if hasattr(captured[0], "data") else str(captured[0])
    assert "nb-theme-df" in html
    assert "transparent" in html
