# Analysis — mpo_sparse

Source JSON: `h1a_mpo_sparse.json`

## Hypothesis

MPO with production sparse reward (mpo_sparse).

## Setup

Agent: mpo; run_dir: `D:\code\sem-proj-asc\backend\autonomous_control\models\ml_overnight_h1a_mpo_sparse_23-20-15`

## Primary KPI

learning_mode=False; train=[-240.03594386310058, -243.49999821185384, -243.49999995230627, -243.49999999999, -243.49999999999, -243.49999999999, -243.49999999999]

## Eval

eval_return_mean=-243.49999999999

## Stability

KL/η: {'kl_mean_last': 403763.375, 'kl_mean_over_train': 407239.2183056923, 'eta_mean_last': 4814309.0, 'n_train_updates_last_ep': 968}

## Verdict

inconclusive

## Next

Compare H1a vs H1b for η dual stability.

## Artifacts

{'videos': [{'kind': 'train', 'episode_idx': 0, 'rank': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1a_mpo_sparse_23-20-15\\videos\\train_ep_0_rank1.mp4'}, {'kind': 'train', 'episode_idx': 1, 'rank': 2, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1a_mpo_sparse_23-20-15\\videos\\train_ep_1_rank2.mp4'}, {'kind': 'train', 'episode_idx': 2, 'rank': 3, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1a_mpo_sparse_23-20-15\\videos\\train_ep_2_rank3.mp4'}, {'kind': 'eval', 'episode_idx': 0, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1a_mpo_sparse_23-20-15\\videos\\eval_ep_0.mp4'}, {'kind': 'eval', 'episode_idx': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h1a_mpo_sparse_23-20-15\\videos\\eval_ep_1.mp4'}]}
