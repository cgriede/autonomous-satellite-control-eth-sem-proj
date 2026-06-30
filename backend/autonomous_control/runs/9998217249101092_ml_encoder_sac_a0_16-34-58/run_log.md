# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `encoder sac a0`
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
- created_utc: `2026-06-29T16:34:58.908218+00:00`

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

- episode_return: `-72.353919`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `60.713737`
- pi_loss_mean: `-10.944434`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-75.588815`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `132.015690`
- pi_loss_mean: `-31.921836`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-77.569253`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `442.202601`
- pi_loss_mean: `-50.664014`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-77.931085`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `781.531138`
- pi_loss_mean: `-67.559689`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-80.215863`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1116.969064`
- pi_loss_mean: `-82.015246`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-80.600564`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1393.447181`
- pi_loss_mean: `-92.597214`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-80.486226`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1420.020007`
- pi_loss_mean: `-97.942727`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-77.725986`
- steps: `516`

### Eval episode 2

- episode_return: `-80.066831`
- steps: `516`

