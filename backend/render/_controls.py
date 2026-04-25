from dataclasses import dataclass
from typing import Callable

import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from environment_definition.constants import RENDER


@dataclass
class RenderControls:
    sim_speed_multiplier: float
    paused: bool = False
    step_backward_cb: Callable[[], None] | None = None
    step_forward_cb: Callable[[], None] | None = None

    def set_speed(self, multiplier: float) -> None:
        self.sim_speed_multiplier = float(multiplier)

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused


def build_controls_panel(fig: plt.Figure, controls: RenderControls) -> dict:
    artists = {}

    button_specs = list(RENDER.speed_button_specs)

    _transport = RENDER.transport_bar_rect
    _btn_h = RENDER.speed_button_height
    _btn_w = RENDER.speed_button_width
    _step_w = 0.052
    _pause_w = 0.072
    _btn_gap = 0.008

    _n_speed = len(button_specs)
    _total_w = (2 * _step_w) + _pause_w + _n_speed * _btn_w + (_n_speed + 2) * _btn_gap
    _start_x = _transport[0] + max(0.0, (_transport[2] - _total_w) * 0.5)
    _btn_y = _transport[1] + max(0.0, (_transport[3] - _btn_h) * 0.5)

    cx = _start_x

    step_back_ax = fig.add_axes([cx, _btn_y, _step_w, _btn_h])
    step_back_ax.set_facecolor(RENDER.space_background)
    artists["step_back"] = Button(
        step_back_ax,
        "<<",
        color=RENDER.speed_button_color,
        hovercolor=RENDER.speed_button_hover_color,
    )
    artists["step_back"].label.set_color(RENDER.speed_button_label_color)
    artists["step_back"].label.set_fontsize(RENDER.speed_button_label_fontsize)
    artists["step_back"].on_clicked(
        lambda _event: controls.step_backward_cb() if (controls.paused and controls.step_backward_cb is not None) else None
    )
    cx += _step_w + _btn_gap

    pause_ax = fig.add_axes([cx, _btn_y, _pause_w, _btn_h])
    pause_ax.set_facecolor(RENDER.space_background)
    artists["pause"] = Button(
        pause_ax,
        "Pause",
        color=RENDER.speed_button_color,
        hovercolor=RENDER.speed_button_hover_color,
    )
    artists["pause"].label.set_color(RENDER.speed_button_label_color)
    artists["pause"].label.set_fontsize(RENDER.speed_button_label_fontsize)
    artists["pause"].on_clicked(
        lambda _event: artists["pause"].label.set_text("Resume" if controls.toggle_pause() else "Pause")
    )

    cx += _pause_w + _btn_gap
    step_fwd_ax = fig.add_axes([cx, _btn_y, _step_w, _btn_h])
    step_fwd_ax.set_facecolor(RENDER.space_background)
    artists["step_fwd"] = Button(
        step_fwd_ax,
        ">>",
        color=RENDER.speed_button_color,
        hovercolor=RENDER.speed_button_hover_color,
    )
    artists["step_fwd"].label.set_color(RENDER.speed_button_label_color)
    artists["step_fwd"].label.set_fontsize(RENDER.speed_button_label_fontsize)
    artists["step_fwd"].on_clicked(
        lambda _event: controls.step_forward_cb() if (controls.paused and controls.step_forward_cb is not None) else None
    )
    cx += _step_w + _btn_gap

    artists["speed"] = []
    for label, multiplier, _ in button_specs:
        ax_btn = fig.add_axes([cx, _btn_y, _btn_w, _btn_h])
        ax_btn.set_facecolor(RENDER.space_background)

        btn = Button(
            ax_btn,
            label,
            color=RENDER.speed_button_color,
            hovercolor=RENDER.speed_button_hover_color,
        )
        btn.label.set_color(RENDER.speed_button_label_color)
        btn.label.set_fontsize(RENDER.speed_button_label_fontsize)
        btn.on_clicked(lambda _event, m=multiplier: controls.set_speed(m))

        artists["speed"].append(btn)
        cx += _btn_w + _btn_gap

    return artists
