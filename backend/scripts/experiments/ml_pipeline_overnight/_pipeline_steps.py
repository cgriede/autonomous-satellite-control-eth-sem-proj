"""Registry of pipeline experiments 3–6 for overnight orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EXPERIMENTS_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PipelineStep:
    step_id: str
    experiment_id: int
    slug: str
    title: str
    runner_name: str
    summary_name: str
    smoke_name: str = "smoke.json"
    blocked_by: str | None = None
    default_argv: tuple[str, ...] = ()
    doc_path: str = ""

    @property
    def folder(self) -> Path:
        return EXPERIMENTS_ROOT / self.slug

    @property
    def runner(self) -> Path:
        return self.folder / self.runner_name

    @property
    def summary(self) -> Path:
        return self.folder / "results" / self.summary_name

    @property
    def smoke(self) -> Path:
        return self.folder / "results" / self.smoke_name


PIPELINE_STEPS: tuple[PipelineStep, ...] = (
    PipelineStep(
        step_id="exp3",
        experiment_id=3,
        slug="ml_sac_mpo_compare",
        title="SAC vs MPO compare",
        runner_name="run_sac_mpo_compare.py",
        summary_name="compare_sac_mpo.json",
        blocked_by=None,
        default_argv=("--show-progress",),
        doc_path="docs/experiments/pipeline/1-built/03-sac-mpo-compare.md",
    ),
    PipelineStep(
        step_id="exp4",
        experiment_id=4,
        slug="ml_agent_reference_pointing",
        title="Agent-reference pointing",
        runner_name="run_agent_reference.py",
        summary_name="agent_reference.json",
        blocked_by="exp3",
        default_argv=("--show-progress", "--arms", "ref0,ref1"),
        doc_path="docs/experiments/pipeline/0-initialized/04-agent-reference-pointing.md",
    ),
    PipelineStep(
        step_id="exp5",
        experiment_id=5,
        slug="ml_mpo_model_size",
        title="MPO model size (S/M/L)",
        runner_name="run_mpo_model_size.py",
        summary_name="mpo_model_size_summary.json",
        blocked_by="exp3",
        default_argv=("--show-progress", "--reward-mode", "sparse"),
        doc_path="docs/experiments/pipeline/0-initialized/05-mpo-model-size.md",
    ),
    PipelineStep(
        step_id="exp6",
        experiment_id=6,
        slug="ml_modular_encoder_r2",
        title="Modular encoder r2",
        runner_name="run_modular_encoder_r2.py",
        summary_name="modular_encoder_r2_summary.json",
        blocked_by="exp5",
        default_argv=("--show-progress",),
        doc_path="docs/experiments/pipeline/0-initialized/06-modular-encoder-r2.md",
    ),
)

STEP_BY_ID: dict[str, PipelineStep] = {s.step_id: s for s in PIPELINE_STEPS}
STEP_ORDER: tuple[str, ...] = tuple(s.step_id for s in PIPELINE_STEPS)


def step_index(step_id: str) -> int:
    try:
        return STEP_ORDER.index(step_id)
    except ValueError as exc:
        raise KeyError(f"Unknown step {step_id!r}; choose from {STEP_ORDER}") from exc


def _smoke_passed(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(data.get("passed"))


def step_readiness(step: PipelineStep) -> dict[str, Any]:
    """Preflight status for orchestrator / long-run-watch."""
    runner_ok = step.runner.is_file()
    smoke_ok = _smoke_passed(step.smoke)
    complete = step.summary.is_file()
    if complete:
        status = "complete"
    elif not runner_ok:
        status = "scaffold_pending"
    elif not smoke_ok:
        status = "smoke_pending"
    else:
        status = "ready"
    return {
        "step_id": step.step_id,
        "slug": step.slug,
        "status": status,
        "runner": str(step.runner),
        "runner_exists": runner_ok,
        "smoke_path": str(step.smoke),
        "smoke_passed": smoke_ok,
        "summary_path": str(step.summary),
        "summary_exists": complete,
    }


def gate_open(step: PipelineStep, *, completed: set[str], ignore_gates: bool) -> tuple[bool, str]:
    if ignore_gates or step.blocked_by is None:
        return True, ""
    if step.blocked_by in completed:
        return True, ""
    blocker = STEP_BY_ID.get(step.blocked_by)
    label = blocker.title if blocker else step.blocked_by
    return False, f"blocked by {step.blocked_by} ({label}) — summary not written yet"


def extract_step_kpis(step: PipelineStep) -> dict[str, Any] | None:
    if not step.summary.is_file():
        return None
    try:
        import json

        return json.loads(step.summary.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


__all__ = [
    "PIPELINE_STEPS",
    "STEP_BY_ID",
    "STEP_ORDER",
    "PipelineStep",
    "extract_step_kpis",
    "gate_open",
    "step_index",
    "step_readiness",
]
