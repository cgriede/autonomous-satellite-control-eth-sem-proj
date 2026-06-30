# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `encoder sac a1`
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
- created_utc: `2026-06-29T16:51:25.623472+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `467.881585`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `397.468337`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `253.995889`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `406.677421`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `439.915993`
- steps: `516`

### Train episode 1

- episode_return: `-75.127287`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `62.016002`
- pi_loss_mean: `-7.513158`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-80.162183`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `136.833451`
- pi_loss_mean: `-27.401487`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-79.855183`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `559.187880`
- pi_loss_mean: `-47.468529`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-81.276115`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1103.820337`
- pi_loss_mean: `-65.180370`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-80.839913`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1757.447233`
- pi_loss_mean: `-82.287068`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-82.976849`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2660.897582`
- pi_loss_mean: `-99.711456`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-81.261594`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3190.098070`
- pi_loss_mean: `-108.741659`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-86.307649`
- steps: `516`

### Eval episode 2

- episode_return: `-86.754175`
- steps: `516`

