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
- created_utc: `2026-06-24T22:48:52.566230+00:00`

## Events

### Warmup episode 1 (random)

- episode_return: `-270775.792411`
- steps: `2903`

### Warmup episode 2 (random)

- episode_return: `-258084.696795`
- steps: `2903`

### Warmup episode 3 (baseline)

- episode_return: `-258772.704243`
- steps: `2903`

### Warmup episode 4 (baseline)

- episode_return: `-258772.704243`
- steps: `2903`

### Train episode 1

- episode_return: `-2300.000000`
- steps: `23`
- n_train_updates: `20`
- q_loss_mean: `17476.178613`
- pi_loss_mean: `-0.129257`
- kl_mean: `3.892488`
- eta_mean: `2.744897`

### Train episode 2

- episode_return: `-2500.000000`
- steps: `25`
- n_train_updates: `25`
- q_loss_mean: `11057.438799`
- pi_loss_mean: `-0.334311`
- kl_mean: `1181.441847`
- eta_mean: `2.816483`

### Train episode 3

- episode_return: `-1900.000000`
- steps: `19`
- n_train_updates: `19`
- q_loss_mean: `1974.015985`
- pi_loss_mean: `-0.546443`
- kl_mean: `17776.560084`
- eta_mean: `2.903579`

### Train episode 4

- episode_return: `-2700.000000`
- steps: `27`
- n_train_updates: `27`
- q_loss_mean: `1204.917304`
- pi_loss_mean: `-0.620695`
- kl_mean: `35104.452546`
- eta_mean: `3.021143`

### Train episode 5

- episode_return: `-1900.000000`
- steps: `19`
- n_train_updates: `19`
- q_loss_mean: `1025.337659`
- pi_loss_mean: `-0.825591`
- kl_mean: `130393.396382`
- eta_mean: `3.152836`

### Train episode 6

- episode_return: `-1900.000000`
- steps: `19`
- n_train_updates: `19`
- q_loss_mean: `943.167047`
- pi_loss_mean: `-0.869653`
- kl_mean: `258787.549342`
- eta_mean: `3.288045`

### Train episode 7

- episode_return: `-1900.000000`
- steps: `19`
- n_train_updates: `19`
- q_loss_mean: `918.222878`
- pi_loss_mean: `-0.869694`
- kl_mean: `287349.447368`
- eta_mean: `3.423889`

### Train episode 8

- episode_return: `-1900.000000`
- steps: `19`
- n_train_updates: `19`
- q_loss_mean: `791.302384`
- pi_loss_mean: `-0.869859`
- kl_mean: `286391.457237`
- eta_mean: `3.549214`

### Train episode 9

- episode_return: `-1900.000000`
- steps: `19`
- n_train_updates: `19`
- q_loss_mean: `803.389395`
- pi_loss_mean: `-0.869763`
- kl_mean: `288582.172697`
- eta_mean: `3.665595`

### Train episode 10

- episode_return: `-1900.000000`
- steps: `19`
- n_train_updates: `19`
- q_loss_mean: `719.204873`
- pi_loss_mean: `-0.869902`
- kl_mean: `288206.826480`
- eta_mean: `3.778590`

### Eval episode 1

- episode_return: `-262582.304842`
- steps: `2903`

### Eval episode 2

- episode_return: `-262582.304842`
- steps: `2903`

