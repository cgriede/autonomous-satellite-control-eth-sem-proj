# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `5`
- train_episodes: `1`
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
- created_utc: `2026-06-27T12:19:52.051673+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `145.409103`
- steps: `1935`

### Warmup episode 2 (baseline overflight)

- episode_return: `108.178720`
- steps: `1935`

### Warmup episode 3 (baseline overflight)

- episode_return: `95.183776`
- steps: `1935`

### Warmup episode 4 (baseline overflight)

- episode_return: `46.562585`
- steps: `1935`

### Warmup episode 5 (baseline overflight)

- episode_return: `50.638123`
- steps: `1935`

### Train episode 1

- episode_return: `3.727295`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `3.630275`
- pi_loss_mean: `-0.838266`
- kl_mean: `469335.964970`
- eta_mean: `21.693058`

### Eval episode 1

- episode_return: `6.858962`
- steps: `1935`

