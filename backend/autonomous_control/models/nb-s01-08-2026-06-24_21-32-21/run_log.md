# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `4`
- train_episodes: `10`
- eval_episodes: `2`
- scalar_dim: `3`
- vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- vision_seq_lens: `[100, 200]`
- encoder_output_dim: `180`
- code_embed_dim: `8`
- cnn_embedding_dim: `32`
- feature_attitude_keys: `['body_z_angle_rad', 'omega_sat_rad_s']`
- feature_orbit_keys: `['theta_orbit_rad']`
- feature_vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- sampled_altitude_km: `528.7583065070219`
- created_utc: `2026-06-24T21:32:21.301037+00:00`

## Events

### Warmup episode 1 (random)

- episode_return: `-270775.792411`
- steps: `2903`

### Warmup episode 2 (random)

- episode_return: `-258084.696795`
- steps: `2903`

### Warmup episode 3 (baseline)

- episode_return: `-258772.704243`
- steps: `2903`

### Warmup episode 4 (baseline)

- episode_return: `-258772.704243`
- steps: `2903`

### Train episode 1

- episode_return: `-255144.695033`
- steps: `2903`
- n_train_updates: `2900`
- q_loss_mean: `4225.055285`
- pi_loss_mean: `-0.256083`
- kl_mean: `0.944329`
- eta_mean: `104.621642`

### Train episode 2

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `9159.872035`
- pi_loss_mean: `-0.259910`
- kl_mean: `1.515968`
- eta_mean: `86534.005746`

### Train episode 3

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `15077.069724`
- pi_loss_mean: `-0.259921`
- kl_mean: `1.827154`
- eta_mean: `75690476.929276`

### Train episode 4

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `20286.578234`
- pi_loss_mean: `-0.259917`
- kl_mean: `2.223689`
- eta_mean: `68448787560.785393`

### Train episode 5

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `25000.610587`
- pi_loss_mean: `-0.259916`
- kl_mean: `2.262822`
- eta_mean: `54942943671963.734375`

### Train episode 6

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `30561.600538`
- pi_loss_mean: `-0.259907`
- kl_mean: `2.253075`
- eta_mean: `44321032136427688.000000`

### Train episode 7

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `33202.206487`
- pi_loss_mean: `-0.259911`
- kl_mean: `2.254913`
- eta_mean: `4611741148775548928.000000`

### Train episode 8

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `39289.625156`
- pi_loss_mean: `-0.259918`
- kl_mean: `2.240376`
- eta_mean: `6829730825139912704.000000`

### Train episode 9

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `44165.807788`
- pi_loss_mean: `-0.259912`
- kl_mean: `2.234722`
- eta_mean: `6829730825139912704.000000`

### Train episode 10

- episode_return: `-251078.298669`
- steps: `2903`
- n_train_updates: `2903`
- q_loss_mean: `45472.300605`
- pi_loss_mean: `-0.259914`
- kl_mean: `2.232637`
- eta_mean: `6829730825139912704.000000`

### Eval episode 1

- episode_return: `-251078.298669`
- steps: `2903`

### Eval episode 2

- episode_return: `-251078.298669`
- steps: `2903`

