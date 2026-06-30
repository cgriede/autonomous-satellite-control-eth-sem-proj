# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo learn cadence hparams`
- warmup_episodes: `5`
- train_episodes: `10`
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
- created_utc: `2026-06-30T23:23:43.906567+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `482.881585`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `417.468337`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `278.995889`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `421.677421`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `449.915993`
- steps: `516`

### Train episode 1

- episode_return: `-784.490379`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `35.145462`
- pi_loss_mean: `-0.172664`
- kl_mean: `-0.117081`
- eta_mean: `3.121073`

### Train episode 2

- episode_return: `-809.563857`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `64.654685`
- pi_loss_mean: `-0.241156`
- kl_mean: `-0.064703`
- eta_mean: `4.956879`

### Train episode 3

- episode_return: `-561.064418`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `156.283519`
- pi_loss_mean: `-0.303871`
- kl_mean: `0.000553`
- eta_mean: `6.437728`

### Train episode 4

- episode_return: `-250.577941`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `279.313212`
- pi_loss_mean: `-0.342314`
- kl_mean: `0.036082`
- eta_mean: `5.280252`

### Train episode 5

- episode_return: `-92.862448`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `384.978036`
- pi_loss_mean: `-0.381915`
- kl_mean: `0.029516`
- eta_mean: `3.881596`

### Train episode 6

- episode_return: `-73.257455`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `505.978275`
- pi_loss_mean: `-0.408910`
- kl_mean: `0.028066`
- eta_mean: `3.098202`

### Train episode 7

- episode_return: `-38.914295`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `669.002221`
- pi_loss_mean: `-0.434267`
- kl_mean: `0.028311`
- eta_mean: `3.245637`

### Train episode 8

- episode_return: `-65.306956`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `861.836676`
- pi_loss_mean: `-0.455905`
- kl_mean: `0.019140`
- eta_mean: `3.091607`

### Train episode 9

- episode_return: `-49.889072`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `1041.926704`
- pi_loss_mean: `-0.468534`
- kl_mean: `0.014203`
- eta_mean: `3.090595`

### Train episode 10

- episode_return: `-50.713539`
- steps: `516`
- n_train_updates: `510`
- q_loss_mean: `1576.325202`
- pi_loss_mean: `-0.478169`
- kl_mean: `0.013052`
- eta_mean: `2.942819`

### Eval episode 1

- episode_return: `-46.352962`
- steps: `516`

### Eval episode 2

- episode_return: `-46.352962`
- steps: `516`

