# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `10`
- train_episodes: `5`
- eval_episodes: `2`
- scalar_dim: `54`
- vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- vision_seq_lens: `[100, 200]`
- encoder_output_dim: `180`
- code_embed_dim: `8`
- cnn_embedding_dim: `32`
- feature_attitude_keys: `['body_z_angle_rad', 'omega_sat_rad_s']`
- feature_orbit_keys: `['theta_orbit_rad']`
- feature_vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- sampled_altitude_km: `528.7583065070219`
- created_utc: `2026-06-26T09:12:30.645800+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 2 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 3 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 4 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 5 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 6 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 7 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 8 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 9 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Warmup episode 10 (baseline overflight)

- episode_return: `140.590923`
- steps: `2903`

### Train episode 1

- episode_return: `0.000000`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `1.169752`
- pi_loss_mean: `-0.859818`
- kl_mean: `221636.324584`
- eta_mean: `85.554130`

### Train episode 2

- episode_return: `0.000000`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `0.239919`
- pi_loss_mean: `-0.869827`
- kl_mean: `287936.892433`
- eta_mean: `67155.126415`

### Train episode 3

- episode_return: `0.000000`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `0.229256`
- pi_loss_mean: `-0.869835`
- kl_mean: `347614.061763`
- eta_mean: `60691192.394118`

