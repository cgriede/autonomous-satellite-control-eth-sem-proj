# Analysis — mpo_dense_latent_10x_shutter

Source JSON: `h6_mpo_dense_latent.json`

## Hypothesis

Dense latent every step + 10× applied shutter credit unblocks MPO learning.

## Setup

run_dir: `D:\code\sem-proj-asc\backend\autonomous_control\models\ml_overnight_h6_mpo_dense_latent_00-05-01`; warmup cache rebuilt for reward fingerprint.

## Primary KPI

learning_mode=False; train=[-240.03594387296823, -243.49999821185384, -243.49999995230627, -243.49999999999, -243.49999999999, -243.49999999999, -243.49999999999]

## H6 diagnostics

{'mean_positive_reward_steps': 0.0, 'train_return_integral': -1701.0359420370883, 'train_returns': [-240.03594387296823, -243.49999821185384, -243.49999995230627, -243.49999999999, -243.49999999999, -243.49999999999, -243.49999999999]}

## Eval

eval_return_mean=-243.49999999999

## Compare H1

Contrast with h1a/h1b sparse arms on same dt profile.

## Verdict

inconclusive

## Artifacts

{'videos': [{'kind': 'train', 'episode_idx': 0, 'rank': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h6_mpo_dense_latent_00-05-01\\videos\\train_ep_0_rank1.mp4'}, {'kind': 'train', 'episode_idx': 1, 'rank': 2, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h6_mpo_dense_latent_00-05-01\\videos\\train_ep_1_rank2.mp4'}, {'kind': 'train', 'episode_idx': 2, 'rank': 3, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h6_mpo_dense_latent_00-05-01\\videos\\train_ep_2_rank3.mp4'}, {'kind': 'eval', 'episode_idx': 0, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h6_mpo_dense_latent_00-05-01\\videos\\eval_ep_0.mp4'}, {'kind': 'eval', 'episode_idx': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h6_mpo_dense_latent_00-05-01\\videos\\eval_ep_1.mp4'}]}
