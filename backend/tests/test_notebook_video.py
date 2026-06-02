"""Tests for notebook MP4 display helpers."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_play_saved_video_uses_file_uri(monkeypatch, tmp_path: Path) -> None:
    from utils.notebook import video as nv

    mp4 = tmp_path / "clip.mp4"
    mp4.write_bytes(b"\x00" * 64)
    monkeypatch.setattr(nv, "ensure_notebook_playable_mp4", lambda _p: (True, "already_h264"))
    monkeypatch.setattr(nv, "log_exported_video", lambda *_a, **_k: None)

    captured: dict[str, str] = {}

    class FakeHTML:
        def __init__(self, data: str) -> None:
            captured["html"] = data

    class FakeDisplay:
        @staticmethod
        def HTML(data: str) -> FakeHTML:
            return FakeHTML(data)

        @staticmethod
        def clear_output(*_a, **_k) -> None:
            return None

        @staticmethod
        def display(_obj) -> None:
            return None

    monkeypatch.setattr(nv, "VIDEO_WIDGET_OUT", None)
    import IPython.display as ipd

    monkeypatch.setattr(ipd, "HTML", FakeDisplay.HTML)
    monkeypatch.setattr(ipd, "clear_output", FakeDisplay.clear_output)
    monkeypatch.setattr(ipd, "display", FakeDisplay.display)

    nv.play_saved_video(mp4, width=640)
    assert mp4.as_uri() in captured["html"]
    assert 'width="640"' in captured["html"]


def test_ensure_notebook_playable_skips_h264(monkeypatch, tmp_path: Path) -> None:
    from utils.notebook import video as nv

    mp4 = tmp_path / "ok.mp4"
    mp4.write_bytes(b"x")
    monkeypatch.setattr(nv, "_video_codec_name", lambda _p: "h264")
    ok, detail = nv.ensure_notebook_playable_mp4(mp4)
    assert ok is True
    assert detail == "already_h264"
