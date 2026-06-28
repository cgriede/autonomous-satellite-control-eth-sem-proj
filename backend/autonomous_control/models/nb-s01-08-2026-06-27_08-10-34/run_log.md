# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `5`
- train_episodes: `3`
- eval_episodes: `1`
- scalar_dim: `55`
- vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- vision_seq_lens: `[100, 200]`
- encoder_output_dim: `180`
- code_embed_dim: `8`
- cnn_embedding_dim: `32`
- feature_attitude_keys: `['body_z_angle_rad', 'omega_sat_rad_s']`
- feature_orbit_keys: `['theta_orbit_rad', 'primary_camera_image_quality']`
- feature_vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- sampled_altitude_km: `528.7583065070219`
- created_utc: `2026-06-27T08:10:34.983507+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `140.646953`
- steps: `2903`

### Warmup episode 2 (baseline overflight)

- episode_return: `108.478650`
- steps: `2903`

### Warmup episode 3 (baseline overflight)

- episode_return: `94.696214`
- steps: `2903`

### Warmup episode 4 (baseline overflight)

- episode_return: `46.566628`
- steps: `2903`

### Warmup episode 5 (baseline overflight)

- episode_return: `50.749666`
- steps: `2903`

### Train episode 1

- episode_return: `0.000000`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `2.475775`
- pi_loss_mean: `-0.850939`
- kl_mean: `634686.231036`
- eta_mean: `125.389097`

### Train episode 2

- episode_return: `0.000000`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `1.011037`
- pi_loss_mean: `-0.869767`
- kl_mean: `1177910.612750`
- eta_mean: `105494.703599`

### Train episode 3

- episode_return: `0.000000`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `1.069659`
- pi_loss_mean: `-0.869823`
- kl_mean: `1805331.247653`
- eta_mean: `87242837.424927`

### Eval episode 1

- episode_return: `0.000000`
- steps: `2903`

