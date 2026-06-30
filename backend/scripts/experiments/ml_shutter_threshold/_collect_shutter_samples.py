"""Record shutter gym / unit / fired at each controller decision."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import autonomous_control.episode_runner as episode_runner

from autonomous_control.action_adapter import shutter_cmd_from_gym, shutter_gym_to_unit_interval

_ACTIVE: "ShutterSampleCollector | None" = None
_ORIG_POLICY_OUTPUT: Any = None
_ORIG_RUN_SERIAL: Any = None


@dataclass
class ShutterSample:
    episode_idx: int
    step_idx: int
    shutter_gym: float
    shutter_unit: float
    fired: bool
    threshold: float


@dataclass
class ShutterSampleCollector:
    threshold: float
    samples: list[ShutterSample] = field(default_factory=list)
    _episode_idx: int = 0
    _step_idx: int = 0
    _patched: bool = False

    def begin_episode(self, episode_idx: int) -> None:
        self._episode_idx = int(episode_idx)
        self._step_idx = 0

    def advance_step(self) -> None:
        self._step_idx += 1

    def shutter_cmds_in_episode(self, episode_idx: int) -> int:
        return sum(1 for s in self.samples if s.episode_idx == episode_idx and s.fired)

    def activate(self) -> None:
        global _ACTIVE, _ORIG_POLICY_OUTPUT, _ORIG_RUN_SERIAL
        if self._patched:
            return
        _ACTIVE = self
        _ORIG_POLICY_OUTPUT = episode_runner.policy_output_to_gym_action
        threshold = float(self.threshold)
        collector = self

        def _wrapped(raw: Any, *, tau_limit: Any = None, active_threshold: float = threshold) -> Any:
            parsed, stored = _ORIG_POLICY_OUTPUT(
                raw, tau_limit=tau_limit, active_threshold=active_threshold
            )
            gym = float(stored[1]) if len(stored) > 1 else -1.0
            unit = shutter_gym_to_unit_interval(gym)
            fired = shutter_cmd_from_gym(gym, threshold=active_threshold)
            collector.samples.append(
                ShutterSample(
                    episode_idx=collector._episode_idx,
                    step_idx=collector._step_idx,
                    shutter_gym=gym,
                    shutter_unit=unit,
                    fired=fired,
                    threshold=float(active_threshold),
                )
            )
            collector._step_idx += 1
            return parsed, stored

        episode_runner.policy_output_to_gym_action = _wrapped  # type: ignore[assignment]

        _ORIG_RUN_SERIAL = episode_runner.EpisodeRunner.run_serial

        def _run_serial(self_runner: Any, agent: Any, **kwargs: Any) -> Any:
            mode = kwargs.get("mode", "train")
            ep_idx = int(kwargs.get("episode_idx", 0))
            if _ACTIVE is not None and mode == "train":
                _ACTIVE.begin_episode(ep_idx)
            return _ORIG_RUN_SERIAL(self_runner, agent, **kwargs)

        episode_runner.EpisodeRunner.run_serial = _run_serial  # type: ignore[method-assign]
        self._patched = True

    def deactivate(self) -> None:
        global _ACTIVE, _ORIG_POLICY_OUTPUT, _ORIG_RUN_SERIAL
        if not self._patched:
            return
        if _ORIG_POLICY_OUTPUT is not None:
            episode_runner.policy_output_to_gym_action = _ORIG_POLICY_OUTPUT  # type: ignore[assignment]
        if _ORIG_RUN_SERIAL is not None:
            episode_runner.EpisodeRunner.run_serial = _ORIG_RUN_SERIAL  # type: ignore[method-assign]
        _ACTIVE = None
        _ORIG_POLICY_OUTPUT = None
        _ORIG_RUN_SERIAL = None
        self._patched = False
