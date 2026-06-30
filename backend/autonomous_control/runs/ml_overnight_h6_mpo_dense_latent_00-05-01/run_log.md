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
- created_utc: `2026-06-29T00:05:02.019344+00:00`

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

- episode_return: `-240.035944`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `53.835531`
- pi_loss_mean: `-0.788812`
- kl_mean: `261256.616026`
- eta_mean: `7.015699`

### Train episode 2

- episode_return: `-243.499998`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `359.043084`
- pi_loss_mean: `-0.869829`
- kl_mean: `348755.378357`
- eta_mean: `37.407293`

### Train episode 3

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `695.761445`
- pi_loss_mean: `-0.869825`
- kl_mean: `366125.820474`
- eta_mean: `272.402549`

### Train episode 4

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `793.666278`
- pi_loss_mean: `-0.869830`
- kl_mean: `377899.786641`
- eta_mean: `2343.175255`

### Train episode 5

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `862.384251`
- pi_loss_mean: `-0.869836`
- kl_mean: `385008.194376`
- eta_mean: `21419.209345`

### Train episode 6

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `789.880688`
- pi_loss_mean: `-0.869838`
- kl_mean: `397522.090748`
- eta_mean: `201873.106054`

### Train episode 7

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `676.416932`
- pi_loss_mean: `-0.869834`
- kl_mean: `407266.180333`
- eta_mean: `1915228.496546`

### Eval episode 1

- episode_return: `-243.500000`
- steps: `1935`

### Eval episode 2

- episode_return: `-243.500000`
- steps: `1935`

