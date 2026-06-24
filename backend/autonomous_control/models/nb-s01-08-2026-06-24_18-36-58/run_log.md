# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `4`
- train_episodes: `10`
- eval_episodes: `2`
- scalar_dim: `3`
- vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- vision_seq_lens: `[100, 200]`
- encoder_output_dim: `180`
- code_embed_dim: `8`
- cnn_embedding_dim: `32`
- feature_attitude_keys: `['body_z_angle_rad', 'omega_sat_rad_s']`
- feature_orbit_keys: `['theta_orbit_rad']`
- feature_vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- sampled_altitude_km: `528.7583065070219`
- created_utc: `2026-06-24T18:36:58.035310+00:00`

## Events

### Warmup episode 1 (random)

- episode_return: `-189700.000000`
- steps: `1897`

### Warmup episode 2 (random)

- episode_return: `-189700.000000`
- steps: `1897`

### Warmup episode 3 (baseline)

- episode_return: `-189700.000000`
- steps: `1897`

### Warmup episode 4 (baseline)

- episode_return: `-189700.000000`
- steps: `1897`

### Train episode 1

- episode_return: `-189700.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `480.193086`
- pi_loss_mean: `-0.428322`
- kl_mean: `92367.010429`
- eta_mean: `19.825093`

### Train episode 2

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `1105.403821`
- pi_loss_mean: `-0.434918`
- kl_mean: `119485.210785`
- eta_mean: `1088.555339`

### Train episode 3

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `3208.266224`
- pi_loss_mean: `-0.434914`
- kl_mean: `134136.227366`
- eta_mean: `87451.989765`

### Train episode 4

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `7313.402000`
- pi_loss_mean: `-0.434913`
- kl_mean: `142964.797155`
- eta_mean: `7111556.657321`

### Train episode 5

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `11644.577499`
- pi_loss_mean: `-0.434913`
- kl_mean: `143026.630576`
- eta_mean: `566911363.848181`

### Train episode 6

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `14527.679022`
- pi_loss_mean: `-0.434921`
- kl_mean: `143469.572594`
- eta_mean: `45337868809.581444`

### Train episode 7

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `20197.891286`
- pi_loss_mean: `-0.434915`
- kl_mean: `160925.986657`
- eta_mean: `3920915429143.886230`

### Train episode 8

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `22723.165329`
- pi_loss_mean: `-0.434918`
- kl_mean: `164816.291105`
- eta_mean: `75080216892745.812500`

### Train episode 9

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `28511.191009`
- pi_loss_mean: `-0.434911`
- kl_mean: `164828.268014`
- eta_mean: `93585013735424.000000`

### Train episode 10

- episode_return: `-189600.000000`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `32834.304889`
- pi_loss_mean: `-0.434918`
- kl_mean: `164982.989296`
- eta_mean: `93585013735424.000000`

### Eval episode 1

- episode_return: `-189600.000000`
- steps: `1897`

### Eval episode 2

- episode_return: `-189600.000000`
- steps: `1897`

