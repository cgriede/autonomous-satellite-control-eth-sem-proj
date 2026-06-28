# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
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
- created_utc: `2026-06-28T13:42:21.514832+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `533.227990`
- steps: `1935`

### Warmup episode 2 (baseline overflight)

- episode_return: `448.678231`
- steps: `1935`

### Warmup episode 3 (baseline overflight)

- episode_return: `297.465809`
- steps: `1935`

### Warmup episode 4 (baseline overflight)

- episode_return: `482.389427`
- steps: `1935`

### Warmup episode 5 (baseline overflight)

- episode_return: `532.202996`
- steps: `1935`

### Train episode 1

- episode_return: `-239.657866`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `53.471485`
- pi_loss_mean: `-0.783003`
- kl_mean: `354769.622792`
- eta_mean: `7.401393`

### Train episode 2

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `351.865784`
- pi_loss_mean: `-0.869819`
- kl_mean: `463980.828254`
- eta_mean: `39.119444`

### Train episode 3

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `751.322168`
- pi_loss_mean: `-0.869821`
- kl_mean: `464734.327124`
- eta_mean: `275.914007`

### Eval episode 1

- episode_return: `-243.500000`
- steps: `1935`

