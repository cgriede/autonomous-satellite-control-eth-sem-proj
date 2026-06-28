"""Branch B run 3: controller-only store + lower shutter threshold (combined fork)."""

from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import autonomous_control.action_adapter as action_adapter  # noqa: E402
import autonomous_control.baseline_overflight_step as baseline_overflight_step  # noqa: E402
import autonomous_control.episode_runner as episode_runner  # noqa: E402

from _runner_common import RESULTS_DIR, run_training_slice, write_analysis_card, write_hypothesis_result  # noqa: E402

_FORK_THRESHOLD = 0.35
_STORE_ALLOW = False
_orig_threshold = action_adapter.DEFAULT_SHUTTER_THRESHOLD
_orig_policy_output = episode_runner.policy_output_to_gym_action
_orig_baseline_tick = baseline_overflight_step.baseline_overflight_controller_tick


def _mark_controller_tick(**_kwargs):
    global _STORE_ALLOW
    _STORE_ALLOW = True


def _patched_policy_output(raw, *, tau_limit=None, active_threshold=_FORK_THRESHOLD):
    _mark_controller_tick()
    return _orig_policy_output(raw, tau_limit=tau_limit, active_threshold=active_threshold)


def _patched_baseline_tick(*args, **kwargs):
    out = _orig_baseline_tick(*args, **kwargs)
    _mark_controller_tick()
    return out


def _agent_setup_hook(setup):
    agent = setup.agent
    runner = setup.runner
    _orig_store = agent.store
    _orig_run_serial = runner.run_serial

    def _gated_store(transition):
        global _STORE_ALLOW
        if not getattr(agent, "_gate_replay_store", False):
            return _orig_store(transition)
        if not _STORE_ALLOW:
            return
        _STORE_ALLOW = False
        return _orig_store(transition)

    def _run_serial_with_store_gate(*args, **kwargs):
        agent._gate_replay_store = True
        try:
            return _orig_run_serial(*args, **kwargs)
        finally:
            agent._gate_replay_store = False

    agent.store = _gated_store  # type: ignore[method-assign]
    runner.run_serial = _run_serial_with_store_gate  # type: ignore[method-assign]


def main() -> None:
    action_adapter.DEFAULT_SHUTTER_THRESHOLD = _FORK_THRESHOLD
    episode_runner.policy_output_to_gym_action = _patched_policy_output
    baseline_overflight_step.baseline_overflight_controller_tick = _patched_baseline_tick
    try:
        kpis = run_training_slice(
            run_id="ml_ls_b3_combined",
            show_progress=False,
            agent_setup_hook=_agent_setup_hook,
        )
    finally:
        action_adapter.DEFAULT_SHUTTER_THRESHOLD = _orig_threshold
        episode_runner.policy_output_to_gym_action = _orig_policy_output
        baseline_overflight_step.baseline_overflight_controller_tick = _orig_baseline_tick

    signal = kpis["increasing_signal"]
    verdict = "supported" if signal["strong_lead"] else "inconclusive"
    out = RESULTS_DIR / "b3_combined.json"
    write_hypothesis_result(
        out,
        experiment_id="ml_learning_signal",
        hypothesis_id="bug_hunt_combined",
        phase="B3",
        frozen_input={
            "fork": f"threshold={_FORK_THRESHOLD}, controller-only store",
        },
        control=None,
        treatment={"kpis": kpis},
        delta={"strong_lead": signal["strong_lead"]},
        parity={"required": True, "passed": False, "notes": "combined fork"},
        instrumentation={"hooks_valid": True},
        debug_examples={"train_episodes": kpis["debug_episodes"]},
        files_changed=[str(Path(__file__))],
        verdict=verdict,
        closeout="Bug-hunt: combined threshold + store gate.",
    )
    write_analysis_card(
        RESULTS_DIR / "bug_hunt_analysis.md",
        hypothesis_id="bug_hunt_combined",
        json_path=out,
        sections={
            "1 Intervention": f"Threshold {_orig_threshold}→{_FORK_THRESHOLD} + controller-only replay store",
            "2 Train returns": str(signal["train_returns_ep1_ep3"]),
            "3 Verdict": verdict,
        },
    )
    print(f"Wrote {out} returns={signal['train_returns_ep1_ep3']} strong_lead={signal['strong_lead']}")


if __name__ == "__main__":
    main()
