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
- created_utc: `2026-06-28T23:42:59.405632+00:00`

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

- episode_return: `-241.011458`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `54.498815`
- pi_loss_mean: `-0.799862`
- kl_mean: `240856.100351`
- eta_mean: `1.000000`

### Train episode 2

- episode_return: `-243.499999`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `352.041314`
- pi_loss_mean: `-0.869829`
- kl_mean: `298961.151230`
- eta_mean: `1.000000`

### Train episode 3

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `724.889636`
- pi_loss_mean: `-0.869825`
- kl_mean: `311337.913142`
- eta_mean: `1.000000`

### Train episode 4

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `934.009649`
- pi_loss_mean: `-0.869830`
- kl_mean: `317446.981502`
- eta_mean: `1.000000`

### Train episode 5

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `1039.069188`
- pi_loss_mean: `-0.869836`
- kl_mean: `323222.903732`
- eta_mean: `1.000000`

### Train episode 6

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `970.492976`
- pi_loss_mean: `-0.869838`
- kl_mean: `338181.590845`
- eta_mean: `1.000000`

### Train episode 7

- episode_return: `-243.500000`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `861.883864`
- pi_loss_mean: `-0.869834`
- kl_mean: `347840.599238`
- eta_mean: `1.000000`

### Eval episode 1

- episode_return: `-243.500000`
- steps: `1935`

### Eval episode 2

- episode_return: `-243.500000`
- steps: `1935`

