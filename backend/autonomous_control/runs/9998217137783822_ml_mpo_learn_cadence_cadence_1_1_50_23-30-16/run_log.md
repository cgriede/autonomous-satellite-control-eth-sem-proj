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
- created_utc: `2026-06-30T23:30:16.178176+00:00`

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

- episode_return: `-912.595822`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `35.428022`
- pi_loss_mean: `-0.173226`
- kl_mean: `-0.117081`
- eta_mean: `3.107877`

### Train episode 2

- episode_return: `-843.952112`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `51.431122`
- pi_loss_mean: `-0.239931`
- kl_mean: `-0.067730`
- eta_mean: `4.478774`

### Train episode 3

- episode_return: `-480.758883`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `102.299043`
- pi_loss_mean: `-0.303786`
- kl_mean: `0.001255`
- eta_mean: `5.124509`

### Train episode 4

- episode_return: `-261.889168`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `158.186902`
- pi_loss_mean: `-0.347396`
- kl_mean: `0.039876`
- eta_mean: `4.147334`

### Train episode 5

- episode_return: `-108.254094`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `238.355976`
- pi_loss_mean: `-0.398411`
- kl_mean: `0.037619`
- eta_mean: `3.050842`

### Train episode 6

- episode_return: `-104.603311`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `376.912905`
- pi_loss_mean: `-0.440105`
- kl_mean: `0.027967`
- eta_mean: `2.312007`

### Train episode 7

- episode_return: `-55.759292`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `517.901362`
- pi_loss_mean: `-0.467349`
- kl_mean: `0.017887`
- eta_mean: `1.786276`

### Train episode 8

- episode_return: `-31.385013`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `688.514485`
- pi_loss_mean: `-0.482024`
- kl_mean: `0.010992`
- eta_mean: `1.371803`

### Train episode 9

- episode_return: `-45.208500`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `879.557084`
- pi_loss_mean: `-0.489461`
- kl_mean: `0.008446`
- eta_mean: `1.119478`

### Train episode 10

- episode_return: `-51.375020`
- steps: `516`
- n_train_updates: `500`
- q_loss_mean: `1121.418696`
- pi_loss_mean: `-0.494338`
- kl_mean: `0.008521`
- eta_mean: `0.981925`

### Eval episode 1

- episode_return: `-15.414815`
- steps: `516`

### Eval episode 2

- episode_return: `-15.414815`
- steps: `516`

