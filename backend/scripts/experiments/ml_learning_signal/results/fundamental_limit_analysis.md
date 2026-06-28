# Analysis — fundamental_limit

Source JSON: `a1_fundamental.json`

## 1 Hypothesis

Sparse capture-only reward + binary shutter threshold + Gaussian exploration cannot reliably produce non-zero increasing train returns in 3 episodes despite warm replay buffer.

## 2 Falsification criteria

Any run with strong_lead=true (all 3 train returns >0 and ep2 or ep3 > ep1).

## 3 Baseline warmup

Cached baseline overflight: returns [145.08638823767077, 108.34964246510562, 95.43579973508072, 47.01253258538355, 50.63812323407264] (mean 89.3). Shutter cmds per ep: [10, 10, 9, 9, 6].

## 4 Shutter exploration (rejects P(fire)≈0)

Fresh policy train-mode samples: p_shutter_fire=0.7734 (n=5000), shutter_gym_mean=0.507. Exploration fires often; problem is timing not reachability.

## 5 Reward sparsity & buffer

Warmup buffer: 14 positive / 9675 transitions (0.145%); shutter=+1 actions: 44 (0.455%).

## 6 On-policy train episode 0

Steps=37, return=0, shutter_cmds=10 (27.0% rate), positive_reward_steps=0. Episode ended early: capture budget exhausted at step 37/1935.

## 7 KL / eta blow-up

Train ep1–3 KL_mean rises 1.7e5 → 2.4e5 → 1.8e6 (08-10-34); eta_mean 21 → 1355 → 8.7e7. Targets: kl_mu=0.1, kl_sigma=1e-4. Policy collapse / unconstrained dual variable.

## 8 Verdict & mechanism

**supported**. Capture reward requires shutter at target overflight geometry. Warmup buffer holds 14/9675 (0.14%) positive transitions from baseline-timed shutters; a fresh policy samples shutter-open ~77% of actions but on-policy train ep0 fires 10 shutters in 37 steps, exhausting capture budget with 0 reward. MPO mixes off-policy positives with on-policy zeros; KL vs targets 0.1/1e-4 blows to 1e5–1e11 by ep3 — 3 episodes cannot yield a reliable increasing train curve.
