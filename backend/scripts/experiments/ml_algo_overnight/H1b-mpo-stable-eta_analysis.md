# Analysis — mpo_sparse_stable_eta

Source JSON: `h1b_mpo_stable_eta.json`

## Hypothesis

MPO with production sparse reward (mpo_sparse_stable_eta).

## Setup

Agent: mpo; run_dir: `D:\code\sem-proj-asc\backend\autonomous_control\models\ml_overnight_h1b_mpo_stable_eta_23-42-59`

## Primary KPI

learning_mode=False; train=[-241.01145775642388, -243.49999921320904, -243.49999997614816, -243.49999999999, -243.49999999999, -243.49999999999, -243.49999999999]

## Eval

eval_return_mean=-243.49999999999

## Stability

KL/η: {'kl_mean_last': 346905.21875, 'kl_mean_over_train': 347455.52065859525, 'eta_mean_last': 1.0, 'n_train_updates_last_ep': 968}

## Verdict

inconclusive

## Next

Compare H1a vs H1b for η dual stability.

## Artifacts

{'videos': [{'kind': 'train', 'episode_idx': 0, 'rank': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1b_mpo_stable_eta_23-42-59\\videos\\train_ep_0_rank1.mp4'}, {'kind': 'train', 'episode_idx': 1, 'rank': 2, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1b_mpo_stable_eta_23-42-59\\videos\\train_ep_1_rank2.mp4'}, {'kind': 'train', 'episode_idx': 2, 'rank': 3, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1b_mpo_stable_eta_23-42-59\\videos\\train_ep_2_rank3.mp4'}, {'kind': 'eval', 'episode_idx': 0, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1b_mpo_stable_eta_23-42-59\\videos\\eval_ep_0.mp4'}, {'kind': 'eval', 'episode_idx': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1b_mpo_stable_eta_23-42-59\\videos\\eval_ep_1.mp4'}]}
