"""Patience early-abort training loop (experiment fork; prod training_workflow unchanged)."""

from __future__ import annotations

from typing import Any

from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw
from tqdm import tqdm


def run_training_with_patience(
    ctx: tw.TrainingWorkflowContext,
    *,
    max_train_episodes: int,
    patience_episodes: int = 10,
) -> dict[str, Any]:
    """Stop if no strict best train return improvement for ``patience_episodes`` in a row."""
    cfg = ctx.config
    best_return = float("-inf")
    best_episode_idx = -1
    episodes_without_improvement = 0
    early_aborted = False
    early_abort_reason: str | None = None

    train_bar = tqdm(
        total=max_train_episodes,
        desc="Train",
        unit="ep",
        disable=not ctx.show_progress,
        position=0,
    )
    if ctx.progress_display is not None:
        ctx.progress_display.set_phase_bar(train_bar)
        ctx.progress_display.set_phase_episode_total(max_train_episodes)
        ctx.progress_display.set_live_feed_interval_steps(cfg.live_feed_interval_steps)

    try:
        for ep in range(max_train_episodes):
            result = tw._ctx_run_episode(
                ctx,
                mode="train",
                train_updates_per_step=cfg.updates_per_step,
                episode_idx=ep,
                show_config_panel=ep == 0,
                early_stop_on_budget_exhausted=cfg.early_stop_on_budget_exhausted,
                np_rng=__import__("numpy").random.default_rng(
                    derive_seed(cfg.seed, "train_episode", ep)
                ),
            )
            ctx.train_results.append(result)
            tw._ctx_record_episode(
                ctx,
                phase="train",
                episode_idx=ep,
                result=result,
                heading=f"Train episode {ep + 1}",
            )
            train_bar.set_postfix(**tw._train_postfix(result))
            train_bar.update(1)

            ep_return = float(result.episode_return)
            if ep_return > best_return:
                best_return = ep_return
                best_episode_idx = ep
                episodes_without_improvement = 0
            else:
                episodes_without_improvement += 1

            completed = ep + 1
            if (
                completed >= patience_episodes
                and episodes_without_improvement >= patience_episodes
            ):
                early_aborted = True
                early_abort_reason = (
                    f"no strict best-return improvement for {patience_episodes} "
                    f"consecutive episodes (best={best_return:.4f} @ ep {best_episode_idx})"
                )
                break
    finally:
        train_bar.close()

    ctx.checkpoint_path = tw._save_checkpoint(ctx.setup.agent, tw.checkpoint_path(ctx.setup.run_dir))
    return {
        "train_episodes_completed": len(ctx.train_results),
        "early_aborted": early_aborted,
        "early_abort_reason": early_abort_reason,
        "best_train_return": best_return if best_episode_idx >= 0 else None,
        "best_train_episode_idx": best_episode_idx if best_episode_idx >= 0 else None,
    }


__all__ = ["run_training_with_patience"]
