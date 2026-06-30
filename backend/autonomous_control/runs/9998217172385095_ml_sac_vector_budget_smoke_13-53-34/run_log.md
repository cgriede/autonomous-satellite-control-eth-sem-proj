# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `sac vector budget smoke`
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
- created_utc: `2026-06-30T13:53:34.905348+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `-31.997284`
- steps: `516`

### Train episode 1

- episode_return: `-130.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.533096`
- pi_loss_mean: `0.418971`
- kl_mean: `nan`
- eta_mean: `nan`

