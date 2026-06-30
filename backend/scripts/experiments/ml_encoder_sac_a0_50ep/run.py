"""Fork: encoder sac_a0 (flat) for extended training (default 50 train episodes)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FORK_ROOT = Path(__file__).resolve().parent
MODULAR_ROOT = FORK_ROOT.parent / "ml_modular_encoder"
BACKEND_DIR = FORK_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
OVERNIGHT_ROOT = FORK_ROOT.parent / "ml_algo_overnight"
for path in (BACKEND_DIR, S01_DIR, MODULAR_ROOT, OVERNIGHT_ROOT, FORK_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import _cpu_budget  # noqa: F401

from _encoder_runner import ArmSpec, append_log, run_sac_arm  # noqa: E402
from _encoder_sim import write_dt_profile  # noqa: E402

PROFILE_PATH = FORK_ROOT / "profile.json"


def _default_train_episodes() -> int:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    return int((profile.get("workflow") or {}).get("train_episodes", 50))


def main() -> None:
    parser = argparse.ArgumentParser(description="encoder sac_a0 extended training fork")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=None)
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    args = parser.parse_args()

    train_episodes = int(args.train_episodes if args.train_episodes is not None else _default_train_episodes())
    write_dt_profile(train_episodes=train_episodes)
    append_log(f"FORK start train_episodes={train_episodes} ref={json.loads(PROFILE_PATH.read_text())['ref_run_id']}")

    spec = ArmSpec("sac_a0", "flat", "encoder_flat_baseline")
    kpis = run_sac_arm(spec, show_progress=args.show_progress, trim_artifacts=args.trim_artifacts)
    print(f"run_dir={kpis['run_dir']}")
    print(f"train_episodes={len(kpis['train_returns'])} eval_mean={kpis['eval_return_mean']:.1f}")


if __name__ == "__main__":
    main()
