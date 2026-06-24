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
- created_utc: `2026-06-24T18:28:54.233996+00:00`

## Events

### Warmup episode 1 (random)

- episode_return: `-189700.000000`
- steps: `1897`

### Warmup episode 2 (random)

- episode_return: `-189330.555130`
- steps: `1897`

### Warmup episode 3 (baseline)

- episode_return: `-189646.137621`
- steps: `1897`

### Warmup episode 4 (baseline)

- episode_return: `-189646.137621`
- steps: `1897`

### Train episode 1

- episode_return: `-189158.497033`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `503.045839`
- pi_loss_mean: `-0.424510`
- kl_mean: `136767.058484`
- eta_mean: `19.751900`

### Train episode 2

- episode_return: `-189205.633454`
- steps: `1897`
- n_train_updates: `1897`
- q_loss_mean: `1171.923785`
- pi_loss_mean: `-0.434902`
- kl_mean: `191340.229705`
- eta_mean: `1129.840558`

