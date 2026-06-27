"""Live training progress: step tqdm + periodic live-stats panel (and optional camera feed)."""

from __future__ import annotations

import io
import sys
from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from tqdm.auto import tqdm

from render._satellite_cam_view import _rgba_for_observation_line_code
from simulation.simulation_info import build_training_live_stats_rows, render_training_panel_html
from simulation.state_types import SimulationTimestepState

from .training_metrics import MetricsSliceStart
from .training_runtime import _in_notebook


@dataclass(frozen=True)
class TrainingProgressConfig:
    live_feed_interval_steps: int = 400
    show_live_stats: bool = True
    show_camera_feed: bool = False
    telemetry_writer: Any | None = None


def _codes_to_strip_image(codes: np.ndarray, *, width_px: int = 32) -> np.ndarray:
    codes = np.asarray(codes, dtype=np.int8).reshape(-1)
    n_bins = int(codes.shape[0])
    col = np.empty((n_bins, 4), dtype=float)
    for j in range(n_bins):
        col[j, :] = _rgba_for_observation_line_code(int(codes[j]))
    return np.tile(col[:, np.newaxis, :], (1, width_px, 1))


class TrainingProgressDisplay:
    """Step-level progress bar and periodic live-stats panel during rollouts."""

    def __init__(
        self,
        *,
        config: TrainingProgressConfig | None = None,
        phase_bar: tqdm | None = None,
        agent: Any | None = None,
    ) -> None:
        self._config = config or TrainingProgressConfig()
        self._phase_bar = phase_bar
        self._agent = agent
        self._step_bar: tqdm | None = None
        self._mode = ""
        self._episode_idx = 0
        self._episode_total: int | None = None
        self._total_steps = 0
        self._metrics_start: MetricsSliceStart | None = None
        self._stats_display_id = "training-live-stats"
        self._feed_display_id = "training-live-feed"
        self._stats_initialized = False
        self._feed_initialized = False
        self._in_notebook = _in_notebook()
        self._live_feed_interval_override: int | None = None
        self._telemetry = self._config.telemetry_writer

    def set_live_feed_interval_steps(self, interval: int) -> None:
        self._live_feed_interval_override = max(1, int(interval))

    def _live_feed_interval(self) -> int:
        if self._live_feed_interval_override is not None:
            return self._live_feed_interval_override
        return max(1, int(self._config.live_feed_interval_steps))

    def set_phase_bar(self, phase_bar: tqdm | None) -> None:
        self._phase_bar = phase_bar

    def set_phase_episode_total(self, episode_total: int | None) -> None:
        self._episode_total = episode_total

    def begin_episode(
        self,
        *,
        mode: str,
        episode_idx: int,
        total_steps: int,
        agent: Any | None = None,
        metrics_start: MetricsSliceStart | None = None,
    ) -> None:
        self._mode = mode
        self._episode_idx = episode_idx
        self._total_steps = int(total_steps)
        if agent is not None:
            self._agent = agent
        self._metrics_start = metrics_start
        if self._step_bar is not None:
            self._step_bar.close()
        self._step_bar = tqdm(
            total=self._total_steps,
            desc=f"{mode} ep {episode_idx + 1}",
            unit="step",
            leave=self._in_notebook,
            dynamic_ncols=True,
            file=sys.stdout,
            position=1 if self._phase_bar is not None else 0,
            mininterval=0.25,
        )

    def on_step(
        self,
        ts: SimulationTimestepState,
        *,
        step: int,
        reward: float,
        episode_return: float,
        done: bool,
        capture_budget_remaining: int | None = None,
        safe_mode_activations: int | None = None,
    ) -> None:
        if self._step_bar is None:
            return
        self._step_bar.update(1)
        interval = self._live_feed_interval()
        if (step % interval) == 0 or done:
            postfix: dict[str, str] = {"return": f"{episode_return:.1f}"}
            if capture_budget_remaining is not None:
                postfix["budget"] = str(int(capture_budget_remaining))
            if safe_mode_activations is not None:
                postfix["safe"] = str(int(safe_mode_activations))
            self._step_bar.set_postfix(**postfix, refresh=False)
            self._step_bar.refresh()
            self._emit_live_update(
                ts,
                step=step,
                reward=reward,
                episode_return=episode_return,
                done=done,
                capture_budget_remaining=capture_budget_remaining,
                safe_mode_activations=safe_mode_activations,
            )

    def end_episode(self) -> None:
        if self._step_bar is not None:
            self._step_bar.close()
            self._step_bar = None
        self._metrics_start = None

    def write(self, msg: str) -> None:
        if self._telemetry is not None:
            self._telemetry.on_training_log(message=msg, mode=self._mode, episode_idx=self._episode_idx)
        if self._step_bar is not None:
            self._step_bar.write(msg)
        elif self._phase_bar is not None:
            self._phase_bar.write(msg)
        else:
            tqdm.write(msg, file=sys.stdout)

    def close(self) -> None:
        self.end_episode()

    def _emit_live_update(
        self,
        ts: SimulationTimestepState,
        *,
        step: int,
        reward: float,
        episode_return: float,
        done: bool,
        capture_budget_remaining: int | None = None,
        safe_mode_activations: int | None = None,
    ) -> None:
        if self._config.show_live_stats:
            self._show_live_stats(
                ts,
                step=step,
                reward=reward,
                episode_return=episode_return,
                done=done,
                capture_budget_remaining=capture_budget_remaining,
                safe_mode_activations=safe_mode_activations,
            )
        if self._config.show_camera_feed:
            primary = np.asarray(ts.camera_observation_line_codes, dtype=np.int8)
            secondary = np.asarray(ts.secondary_camera_observation_line_codes, dtype=np.int8)
            if self._in_notebook:
                self._show_notebook_camera_feed(
                    primary,
                    secondary,
                    step=step,
                    episode_return=episode_return,
                    done=done,
                )
            else:
                self._print_cli_feed(step=step, episode_return=episode_return, done=done)

    def _show_live_stats(
        self,
        ts: SimulationTimestepState,
        *,
        step: int,
        reward: float,
        episode_return: float,
        done: bool,
        capture_budget_remaining: int | None = None,
        safe_mode_activations: int | None = None,
    ) -> None:
        rows = build_training_live_stats_rows(
            ts,
            step=step,
            total_steps=self._total_steps,
            reward=reward,
            episode_return=episode_return,
            mode=self._mode,
            episode_idx=self._episode_idx,
            episode_total=self._episode_total,
            agent=self._agent,
            metrics_start=self._metrics_start,
            capture_budget_remaining=capture_budget_remaining,
            safe_mode_activations=safe_mode_activations,
        )
        if done:
            rows.append(("status", "episode done"))

        if self._telemetry is not None:
            self._telemetry.on_step_snapshot(
                episode_idx=self._episode_idx,
                step_idx=int(step),
                sim_time_s=float(ts.sim_time_s),
                reward=float(reward),
                episode_return=float(episode_return),
                phase=self._mode,
                done=bool(done),
                capture_budget_remaining=capture_budget_remaining,
                safe_mode_activations=safe_mode_activations,
            )

        if self._in_notebook:
            from IPython.display import HTML, display, update_display

            html = render_training_panel_html(rows, title="Live stats")
            payload = HTML(html)
            if self._stats_initialized:
                update_display(payload, display_id=self._stats_display_id)
            else:
                display(payload, display_id=self._stats_display_id)
                self._stats_initialized = True
        elif self._step_bar is not None:
            status = "done" if done else "running"
            self._step_bar.write(
                f"[live stats] {self._mode} ep {self._episode_idx + 1} "
                f"step {step}/{self._total_steps} return={episode_return:.1f} ({status})"
            )

    def _show_notebook_camera_feed(
        self,
        primary: np.ndarray,
        secondary: np.ndarray,
        *,
        step: int,
        episode_return: float,
        done: bool,
    ) -> None:
        from IPython.display import Image, display, update_display

        fig, axes = plt.subplots(
            1,
            2 if secondary.size else 1,
            figsize=(7.0, 1.6),
            gridspec_kw={"wspace": 0.15},
        )
        if secondary.size:
            ax_primary, ax_secondary = axes
        else:
            ax_primary = axes
            ax_secondary = None

        for ax, codes, title in (
            (ax_primary, primary, "Primary"),
            (ax_secondary, secondary, "Secondary"),
        ):
            if ax is None or codes.size == 0:
                continue
            img = _codes_to_strip_image(codes)
            ax.imshow(img, aspect="auto", interpolation="nearest", origin="upper")
            ax.set_title(title, fontsize=9, color="0.85")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor("black")
            for spine in ax.spines.values():
                spine.set_color("0.35")

        status = "done" if done else "running"
        fig.patch.set_facecolor("black")
        fig.suptitle(
            f"{self._mode} ep {self._episode_idx + 1} · step {step} · "
            f"return {episode_return:.1f} · {status}",
            color="0.9",
            fontsize=10,
            y=1.05,
        )
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=110)
        plt.close(fig)
        payload = Image(data=buf.getvalue())
        if self._feed_initialized:
            update_display(payload, display_id=self._feed_display_id)
        else:
            display(payload, display_id=self._feed_display_id)
            self._feed_initialized = True

    def _print_cli_feed(self, *, step: int, episode_return: float, done: bool) -> None:
        if self._step_bar is None:
            return
        status = "done" if done else "running"
        self._step_bar.write(
            f"[camera] {self._mode} ep {self._episode_idx + 1} step {step} "
            f"return={episode_return:.1f} ({status})"
        )
