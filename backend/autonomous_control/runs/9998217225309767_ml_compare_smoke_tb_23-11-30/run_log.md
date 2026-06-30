# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `compare smoke tb`
- warmup_episodes: `1`
- train_episodes: `1`
- eval_episodes: `0`
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
- created_utc: `2026-06-29T23:11:30.233825+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `467.881585`
- steps: `516`

### Train episode 1

- episode_return: `-73.831148`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `48.247745`
- pi_loss_mean: `-2.691503`
- kl_mean: `nan`
- eta_mean: `nan`

