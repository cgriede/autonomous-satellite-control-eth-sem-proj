# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `agent reference ref1`
- warmup_episodes: `5`
- train_episodes: `1`
- eval_episodes: `2`
- scalar_dim: `105`
- vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- vision_seq_lens: `[101, 200]`
- encoder_output_dim: `180`
- code_embed_dim: `8`
- cnn_embedding_dim: `32`
- num_cnn_layers: `2`
- feature_attitude_keys: `['body_z_angle_rad', 'omega_sat_rad_s']`
- feature_orbit_keys: `['theta_orbit_rad', 'primary_camera_image_quality']`
- feature_vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- sampled_altitude_km: `528.7583065070219`
- created_utc: `2026-06-30T10:40:51.094186+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `-41.950589`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `-59.950004`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `-59.939624`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `-40.309062`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `-40.566543`
- steps: `516`

### Train episode 1

- episode_return: `-98.130048`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.364371`
- pi_loss_mean: `0.557735`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `50.698242`
- steps: `516`

### Eval episode 2

- episode_return: `50.698242`
- steps: `516`

