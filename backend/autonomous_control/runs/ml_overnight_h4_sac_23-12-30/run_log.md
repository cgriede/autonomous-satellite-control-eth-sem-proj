# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `5`
- train_episodes: `7`
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
- created_utc: `2026-06-28T23:12:30.978183+00:00`

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

- episode_return: `-131.467385`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `64.034593`
- pi_loss_mean: `-20.497827`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-119.380029`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `470.440277`
- pi_loss_mean: `-53.853791`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-125.229505`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `1141.427557`
- pi_loss_mean: `-86.012815`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-137.936409`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `1838.208018`
- pi_loss_mean: `-119.469544`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-153.957281`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `2326.684495`
- pi_loss_mean: `-146.581733`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-163.314766`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `2674.096867`
- pi_loss_mean: `-157.163801`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-171.462133`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `3037.720315`
- pi_loss_mean: `-162.350721`
- kl_mean: `nan`
- eta_mean: `nan`

