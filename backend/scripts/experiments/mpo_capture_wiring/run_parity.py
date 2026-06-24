"""Experiment: MPO capture wiring parity vs take_picture_verification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from autonomous_control.reward import RewardConfig  # noqa: E402
from simulation.episode_capture import evaluate_shutter_from_arrays  # noqa: E402
from simulation.take_picture import TakePictureBudget, TakePictureConfig  # noqa: E402
from s01_utils import take_picture_verification as tpv  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ctx = tpv.build_take_picture_verification_context(seed=tpv.TAKE_PICTURE_VERIFICATION_SEED)
    series = ctx.target_series
    cmd_step = ctx.capture_step
    reward_cfg = RewardConfig(enable_distance_reward=False, enable_image_quality_capture=True)
    expected = tpv.evaluate_capture_at_step(
        series,
        cmd_step=cmd_step,
        budget=TakePictureBudget.from_config(TakePictureConfig()),
        reward_config=reward_cfg,
    )
    actual = evaluate_shutter_from_arrays(
        cmd_step=cmd_step,
        n_steps=int(series.t_s.shape[0]),
        observation_line_codes=series.camera_observation_line_codes,
        camera_image_quality=series.camera_image_quality,
        camera_cloud_blocked_fraction=series.camera_cloud_blocked_fraction,
        budget=TakePictureBudget.from_config(TakePictureConfig()),
    )
    parity_ok = (
        actual.capture_step == expected.capture_step
        and actual.override.picture_taken == expected.picture_taken
        and actual.override.capture_target_novel == expected.capture_target_novel
        and abs(actual.override.primary_target_pixel_coverage - expected.target_coverage) < 1e-9
    )
    payload = {
        "experiment_id": "mpo_capture_wiring_parity",
        "verdict": "pass" if parity_ok else "fail",
        "cmd_step": cmd_step,
        "expected_capture_reward": expected.capture_reward,
        "budget_remaining": actual.budget_remaining,
    }
    out = RESULTS_DIR / "parity.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out} verdict={payload['verdict']}")
    if not parity_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
