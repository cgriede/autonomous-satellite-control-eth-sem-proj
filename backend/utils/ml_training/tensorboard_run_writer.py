"""Episode-level TensorBoard logging for training workflow runs."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_TRAIN_LOSS_KEYS: tuple[tuple[str, str], ...] = (
    ("train/q_loss_mean", "q_loss_mean"),
    ("train/pi_loss_mean", "pi_loss_mean"),
)
_KL_DETAIL_KEYS: tuple[tuple[str, str], ...] = (
    ("train/kl_mu_mean", "kl_mu_mean"),
    ("train/kl_sigma_mean", "kl_sigma_mean"),
)


@dataclass(frozen=True)
class TensorBoardLogProfile:
    train_return: bool = True
    eval_return: bool = False
    warmup_return: bool = False
    q_pi_loss: bool = True
    kl_mean: bool = True
    kl_detail: bool = False
    eta_mean: bool = True
    buffer_size: bool = False
    n_train_updates: bool = False
    steps: bool = False
    use_hparams: bool = True
    step_level: bool = False


def _is_finite_scalar(value: Any) -> bool:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(parsed)


def _coerce_hparam_value(value: Any) -> str | float | bool | int:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float) and math.isfinite(value):
        return float(value)
    return str(value)


def build_hparams_from_config_snapshot(snapshot: dict[str, Any]) -> dict[str, str | float | bool | int]:
    """Flatten workflow + mpo config snapshot keys for TensorBoard HParams."""
    workflow = snapshot.get("workflow") or {}
    mpo = snapshot.get("mpo") or {}
    out: dict[str, str | float | bool | int] = {}

    for key in (
        "seed",
        "warmup_episodes",
        "train_episodes",
        "eval_episodes",
        "updates_per_step",
        "train_every_n_steps",
        "experiment_name",
    ):
        if key in workflow:
            out[f"workflow/{key}"] = _coerce_hparam_value(workflow[key])

    for key in (
        "buffer_size",
        "batch_size",
        "gamma",
        "tau",
        "learning_rate_q",
        "learning_rate_pi",
        "learning_rate_eta",
        "target_kl_mu",
        "target_kl_sigma",
    ):
        if key in mpo:
            out[f"mpo/{key}"] = _coerce_hparam_value(mpo[key])

    return out


class TensorBoardRunWriter:
    """Writes filtered train scalars and optional HParams under ``run_dir/tensorboard/``."""

    def __init__(self, run_dir: Path, profile: TensorBoardLogProfile | None = None) -> None:
        self._run_dir = run_dir
        self._profile = profile or TensorBoardLogProfile()
        self._log_dir = run_dir / "tensorboard"
        self._writer: Any | None = None
        self._closed = False

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    def _ensure_writer(self) -> Any:
        if self._writer is None:
            from torch.utils.tensorboard import SummaryWriter

            self._log_dir.mkdir(parents=True, exist_ok=True)
            self._writer = SummaryWriter(log_dir=str(self._log_dir))
        return self._writer

    def log_hparams(
        self,
        hparam_dict: dict[str, Any],
        metric_dict: dict[str, float] | None = None,
    ) -> None:
        if not self._profile.use_hparams or not hparam_dict:
            return
        writer = self._ensure_writer()
        hparams = {key: _coerce_hparam_value(value) for key, value in hparam_dict.items()}
        metrics = metric_dict or {"train/episode_return": 0.0}
        writer.add_hparams(hparams, metrics)

    def log_train_episode(
        self,
        episode_idx: int,
        episode_return: float,
        learning_row: dict[str, Any],
    ) -> None:
        writer = self._ensure_writer()
        step = int(episode_idx)
        profile = self._profile

        if profile.train_return:
            writer.add_scalar("train/episode_return", float(episode_return), step)

        if profile.q_pi_loss:
            for tag, key in _TRAIN_LOSS_KEYS:
                if _is_finite_scalar(learning_row.get(key)):
                    writer.add_scalar(tag, float(learning_row[key]), step)

        if profile.kl_mean and _is_finite_scalar(learning_row.get("kl_mean")):
            writer.add_scalar("train/kl_mean", float(learning_row["kl_mean"]), step)

        if profile.kl_detail:
            for tag, key in _KL_DETAIL_KEYS:
                if _is_finite_scalar(learning_row.get(key)):
                    writer.add_scalar(tag, float(learning_row[key]), step)

        if profile.eta_mean and _is_finite_scalar(learning_row.get("eta_mean")):
            writer.add_scalar("train/eta_mean", float(learning_row["eta_mean"]), step)

        if profile.buffer_size and learning_row.get("buffer_size") is not None:
            writer.add_scalar("train/buffer_size", float(learning_row["buffer_size"]), step)

        if profile.n_train_updates and learning_row.get("n_train_updates") is not None:
            writer.add_scalar("train/n_train_updates", float(learning_row["n_train_updates"]), step)

        if profile.steps:
            writer.add_scalar("train/steps", float(learning_row.get("steps", 0)), step)

    def close(self) -> None:
        if self._closed:
            return
        if self._writer is not None:
            self._writer.flush()
            self._writer.close()
            self._writer = None
        self._closed = True


def read_train_scalar_series(log_dir: Path, tag: str) -> dict[int, float]:
    """Read scalar events for ``tag`` from a TensorBoard log directory."""
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    acc = EventAccumulator(str(log_dir))
    acc.Reload()
    return {int(event.step): float(event.value) for event in acc.Scalars(tag)}


def verify_train_return_parity(run_dir: Path, *, atol: float = 1e-4) -> None:
    """Assert ``train/episode_return`` matches train rows in ``episodes.csv``."""
    import csv

    csv_path = run_dir / "episodes.csv"
    tb_dir = run_dir / "tensorboard"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Missing episodes.csv: {csv_path}")
    if not tb_dir.is_dir():
        raise FileNotFoundError(f"Missing tensorboard log dir: {tb_dir}")

    tb_returns = read_train_scalar_series(tb_dir, "train/episode_return")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        train_rows = [row for row in csv.DictReader(handle) if row.get("phase") == "train"]

    for row in train_rows:
        episode_idx = int(row["episode_idx"])
        csv_return = float(row["episode_return"])
        if episode_idx not in tb_returns:
            raise AssertionError(f"Missing TensorBoard train/episode_return for episode {episode_idx}")
        tb_return = tb_returns[episode_idx]
        if abs(csv_return - tb_return) > atol:
            raise AssertionError(
                f"Return mismatch ep {episode_idx}: csv={csv_return} tb={tb_return}"
            )
