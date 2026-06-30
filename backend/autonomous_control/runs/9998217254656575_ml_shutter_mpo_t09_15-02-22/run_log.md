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
- created_utc: `2026-06-29T15:02:23.425983+00:00`

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

- episode_return: `-99.903705`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `60.628273`
- pi_loss_mean: `-0.727621`
- kl_mean: `196654.533014`
- eta_mean: `4.488436`

### Train episode 2

- episode_return: `-101.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `117.291470`
- pi_loss_mean: `-0.869823`
- kl_mean: `303513.708121`
- eta_mean: `10.202601`

### Train episode 3

- episode_return: `-101.599999`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `402.020825`
- pi_loss_mean: `-0.869833`
- kl_mean: `313657.702883`
- eta_mean: `24.146848`

### Train episode 4

- episode_return: `-101.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `650.674543`
- pi_loss_mean: `-0.869826`
- kl_mean: `323100.652011`
- eta_mean: `64.220626`

### Train episode 5

- episode_return: `-101.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `804.108829`
- pi_loss_mean: `-0.869835`
- kl_mean: `330865.159520`
- eta_mean: `186.968741`

### Train episode 6

- episode_return: `-101.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `843.309618`
- pi_loss_mean: `-0.869803`
- kl_mean: `337321.227592`
- eta_mean: `573.598670`

### Train episode 7

- episode_return: `-101.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `741.997045`
- pi_loss_mean: `-0.869844`
- kl_mean: `348791.949310`
- eta_mean: `1831.804022`

### Eval episode 1

- episode_return: `-101.600000`
- steps: `516`

### Eval episode 2

- episode_return: `-101.600000`
- steps: `516`

