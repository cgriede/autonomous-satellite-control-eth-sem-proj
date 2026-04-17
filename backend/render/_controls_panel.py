import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.colors import to_rgba

from environment_definition.constants import RENDER, ureg

def set_sim_speed(multiplier):
    global sim_speed_multiplier
    sim_speed_multiplier = float(multiplier)

def toggle_pause(_event=None):
    global paused, pause_button
    paused = not paused
    # Update label text if the button object exists yet.
    if pause_button is not None:
        pause_button.label.set_text("Resume" if paused else "Pause")

def build_controls_panel(fig: plt.Figure) -> dict:
    global pause_button
    artists = {}

    button_specs = list(RENDER.speed_button_specs)

    _transport = RENDER.transport_bar_rect
    _btn_h = RENDER.speed_button_height
    _btn_w = RENDER.speed_button_width
    _pause_w = 0.072
    _btn_gap = 0.008

    _n_speed = len(button_specs)
    _total_w = _pause_w + _n_speed * _btn_w + _n_speed * _btn_gap
    _start_x = _transport[0] + max(0.0, (_transport[2] - _total_w) * 0.5)
    _btn_y = _transport[1] + max(0.0, (_transport[3] - _btn_h) * 0.5)

    cx = _start_x

    # Pause button
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
    artists["pause"].on_clicked(toggle_pause)
    pause_button = artists["pause"]

    cx += _pause_w + _btn_gap

    # Speed buttons
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
        btn.on_clicked(lambda _event, m=multiplier: set_sim_speed(m))

        artists["speed"].append(btn)
        cx += _btn_w + _btn_gap

    return artists