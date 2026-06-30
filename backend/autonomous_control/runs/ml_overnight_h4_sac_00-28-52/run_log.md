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
- created_utc: `2026-06-29T00:28:52.368658+00:00`

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

- episode_return: `-131.396579`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `63.253058`
- pi_loss_mean: `-20.542209`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-128.657968`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `451.605251`
- pi_loss_mean: `-53.174850`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-115.622140`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `1090.117092`
- pi_loss_mean: `-84.313744`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-138.961973`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `1630.682422`
- pi_loss_mean: `-119.918738`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-153.417297`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `2168.577703`
- pi_loss_mean: `-152.441130`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-157.657959`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `2706.505522`
- pi_loss_mean: `-171.786689`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-159.593602`
- steps: `1935`
- n_train_updates: `968`
- q_loss_mean: `3174.504123`
- pi_loss_mean: `-185.098680`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-167.734594`
- steps: `1935`

### Eval episode 2

- episode_return: `-168.712153`
- steps: `1935`

