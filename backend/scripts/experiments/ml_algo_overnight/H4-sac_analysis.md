# Analysis — sac_entropy_fixed_alpha

Source JSON: `h4_sac.json`

## Hypothesis

Off-policy SAC (fixed α=0.2) learns where MPO fails on sparse EO reward.

## Setup

run_dir: `D:\code\sem-proj-asc\backend\autonomous_control\models\ml_overnight_h4_sac_00-28-52`; reuses production Actor/Critic.

## Primary KPI

learning_mode=True; train=[-131.39657872026422, -128.65796839013697, -115.62214045305998, -138.96197269575822, -153.41729739636364, -157.65795865280887, -159.5936022367072]

## Eval

eval_return_mean=-168.22337354206078

## Compare MPO

Contrast with h1a/h1b/h6 on same dt profile.

## Verdict

supported

## Artifacts

{'videos': [{'kind': 'train', 'episode_idx': 2, 'rank': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h4_sac_00-28-52\\videos\\train_ep_2_rank1.mp4'}, {'kind': 'train', 'episode_idx': 1, 'rank': 2, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h4_sac_00-28-52\\videos\\train_ep_1_rank2.mp4'}, {'kind': 'train', 'episode_idx': 0, 'rank': 3, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h4_sac_00-28-52\\videos\\train_ep_0_rank3.mp4'}, {'kind': 'eval', 'episode_idx': 0, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h4_sac_00-28-52\\videos\\eval_ep_0.mp4'}, {'kind': 'eval', 'episode_idx': 1, 'path': 'D:\\code\\sem-proj-asc\\backend\\autonomous_control\\models\\ml_overnight_h4_sac_00-28-52\\videos\\eval_ep_1.mp4'}]}
