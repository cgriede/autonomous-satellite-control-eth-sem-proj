# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `nb-s01-08`
- warmup_episodes: `5`
- train_episodes: `3`
- eval_episodes: `1`
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
- created_utc: `2026-07-10T12:40:50.723463+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `548.227990`
- steps: `1935`

### Warmup episode 2 (baseline overflight)

- episode_return: `468.678231`
- steps: `1935`

### Warmup episode 3 (baseline overflight)

- episode_return: `322.465809`
- steps: `1935`

### Warmup episode 4 (baseline overflight)

- episode_return: `497.389427`
- steps: `1935`

### Warmup episode 5 (baseline overflight)

- episode_return: `537.202996`
- steps: `1935`

