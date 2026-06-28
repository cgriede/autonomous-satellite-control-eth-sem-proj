# Hypothesis B — wiring bug

**Statement:** A fixable bug in ML wiring (buffer preload, shutter gating, reward index, train/eval mode, action dim) prevents the policy from receiving capture credit during train rollouts.

**Falsification:** If thorough code trace finds no bug and zero-reward episodes have `n_shutter_cmds=0` with correctly wired paths.

**Candidate bugs:**

- Warmup buffer stores shutter gym ±1 but policy explores continuous dim rarely crossing threshold
- Reward applied only when `picture_taken` but agent never triggers `apply_shutter_capture`
- MPO trains on warmup transitions but on-policy rollouts use different action parsing
- `collect_states=False` breaking observation parity (unlikely for return)

**Allowed changes:** experiment forks under `b_bug_hunt/` that monkeypatch or fork runner logic only.

**Success bar:** `strong_lead=true` after minimal fix, or identified one-line production fix ready for promote.
