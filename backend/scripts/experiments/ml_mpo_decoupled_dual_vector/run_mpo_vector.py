"""Exp 11: MPO fixed decoupled-KL dual, sparse reward, vector mode @ dt 1.5s."""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"


def _ensure_experiment_root_first() -> None:
    experiment = str(EXPERIMENT_ROOT)
    while experiment in sys.path:
        sys.path.remove(experiment)
    sys.path.insert(0, experiment)


for path in (BACKEND_DIR, S01_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
_ensure_experiment_root_first()

import _cpu_budget  # noqa: F401

import torch  # noqa: E402

from _sim_constants_fork import write_dt_profile  # noqa: E402
from _profile_baseline import profile  # noqa: E402

_ensure_experiment_root_first()

from _vector_runner import (  # noqa: E402
    RESULTS_DIR,
    append_log,
    run_vector_arm,
    write_hypothesis_result,
)

SUMMARY_JSON = RESULTS_DIR / "mpo_vector.json"
SMOKE_JSON = RESULTS_DIR / "smoke.json"


def run_smoke(*, allow_cpu: bool = False) -> dict:
    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")
    write_dt_profile(train_episodes=1)
    payload = run_vector_arm(smoke=True)
    write_hypothesis_result(
        SMOKE_JSON,
        phase="smoke",
        experiment_id="ml_mpo_decoupled_dual_vector",
        **payload,
    )
    append_log(
        f"SMOKE OK warmup_return={payload['warmup_return']:.1f} "
        f"kl={payload['train_metrics']['kl']:.4g} "
        f"alpha_mu={payload['train_metrics']['alpha_mu']:.4g}"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ml_mpo_decoupled_dual_vector — Exp 11 MPO sparse vector"
    )
    parser.add_argument("--smoke", action="store_true", help="Warmup + one MPO train step")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=None)
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    args = parser.parse_args()

    if args.smoke:
        payload = run_smoke(allow_cpu=args.allow_cpu)
        print(f"Smoke OK → {SMOKE_JSON}")
        print(f"  run_dir: {payload['run_dir']}")
        print(f"  attitude_request_mode: {payload['attitude_request_mode']}")
        print(f"  kl={payload['train_metrics']['kl']:.4g} eta={payload['train_metrics']['eta']:.4g}")
        print(
            f"  alpha_mu={payload['train_metrics']['alpha_mu']:.4g} "
            f"alpha_sigma={payload['train_metrics']['alpha_sigma']:.4g}"
        )
        return

    train_episodes = int(
        args.train_episodes
        if args.train_episodes is not None
        else (profile().get("workflow") or {}).get("train_episodes", 50)
    )
    write_dt_profile(train_episodes=train_episodes)
    append_log(f"RUN start train_episodes={train_episodes} ref={profile().get('ref_run_id')}")

    try:
        kpis = run_vector_arm(
            show_progress=args.show_progress,
            trim_artifacts=args.trim_artifacts,
            train_episodes=train_episodes,
        )
    except Exception as exc:
        err_path = RESULTS_DIR / "vector_sparse_error.json"
        write_hypothesis_result(
            err_path,
            experiment_id="ml_mpo_decoupled_dual_vector",
            arm_id="vector_sparse",
            error=str(exc),
            traceback=traceback.format_exc(),
            verdict="error",
        )
        append_log(f"ERROR: {exc}")
        raise

    summary = {
        "experiment_id": "ml_mpo_decoupled_dual_vector",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "ref_run_id": profile().get("ref_run_id"),
        "train_episodes": train_episodes,
        "reward_mode": "sparse",
        "attitude_request_mode": "vector",
        "arm": kpis,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    signal = kpis.get("learning_signal") or {}
    print(f"Wrote {SUMMARY_JSON}")
    print(
        f"  learning_mode={signal.get('learning_mode')} "
        f"train_best={max(kpis['train_returns']) if kpis['train_returns'] else 0:.1f} "
        f"eval_mean={kpis.get('eval_return_mean', 0):.1f}"
    )
    print(f"  run_dir: {kpis['run_dir']}")


if __name__ == "__main__":
    main()
