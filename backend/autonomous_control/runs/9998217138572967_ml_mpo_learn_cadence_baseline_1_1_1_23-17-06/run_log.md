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
- created_utc: `2026-06-30T23:17:07.033518+00:00`

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

- episode_return: `-743.318314`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `34.950274`
- pi_loss_mean: `-0.173688`
- kl_mean: `-0.116921`
- eta_mean: `3.133883`

### Train episode 2

- episode_return: `-784.883857`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `67.767222`
- pi_loss_mean: `-0.242496`
- kl_mean: `-0.064265`
- eta_mean: `4.710214`

### Train episode 3

- episode_return: `-521.576331`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `149.562277`
- pi_loss_mean: `-0.305373`
- kl_mean: `0.001663`
- eta_mean: `6.204027`

### Train episode 4

- episode_return: `-240.790457`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `289.687769`
- pi_loss_mean: `-0.344408`
- kl_mean: `0.034807`
- eta_mean: `5.167990`

### Train episode 5

- episode_return: `-107.582076`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `453.354996`
- pi_loss_mean: `-0.380636`
- kl_mean: `0.028245`
- eta_mean: `3.863648`

### Train episode 6

- episode_return: `-63.441661`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `654.052913`
- pi_loss_mean: `-0.408421`
- kl_mean: `0.029352`
- eta_mean: `3.634307`

### Train episode 7

- episode_return: `-54.190744`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `776.594225`
- pi_loss_mean: `-0.436873`
- kl_mean: `0.022676`
- eta_mean: `3.695399`

### Train episode 8

- episode_return: `-64.815494`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `898.745666`
- pi_loss_mean: `-0.454054`
- kl_mean: `0.016001`
- eta_mean: `3.503648`

### Train episode 9

- episode_return: `-26.087352`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1110.154560`
- pi_loss_mean: `-0.466291`
- kl_mean: `0.016919`
- eta_mean: `3.766366`

### Train episode 10

- episode_return: `-22.918132`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1206.708465`
- pi_loss_mean: `-0.476718`
- kl_mean: `0.015372`
- eta_mean: `3.764108`

### Eval episode 1

- episode_return: `-38.567453`
- steps: `516`

### Eval episode 2

- episode_return: `-38.567453`
- steps: `516`

