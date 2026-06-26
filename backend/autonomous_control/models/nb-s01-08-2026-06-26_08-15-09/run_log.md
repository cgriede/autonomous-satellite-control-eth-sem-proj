# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `10`
- train_episodes: `5`
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
- created_utc: `2026-06-26T08:15:09.663682+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 2 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 3 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 4 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 5 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 6 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 7 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 8 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 9 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Warmup episode 10 (baseline overflight)

- episode_return: `-93859.409077`
- steps: `1145`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`

### Train episode 1

- episode_return: `-2900.000000`
- steps: `29`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `29`
- q_loss_mean: `15760.908439`
- pi_loss_mean: `-0.176053`
- kl_mean: `28.677874`
- eta_mean: `2.758283`

### Train episode 2

- episode_return: `-3100.000000`
- steps: `31`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `31`
- q_loss_mean: `5364.799336`
- pi_loss_mean: `-0.472206`
- kl_mean: `9892.338808`
- eta_mean: `2.861253`

### Train episode 3

- episode_return: `-2100.000000`
- steps: `21`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `21`
- q_loss_mean: `1457.538045`
- pi_loss_mean: `-0.590410`
- kl_mean: `31177.807943`
- eta_mean: `2.983215`

### Train episode 4

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `970.419941`
- pi_loss_mean: `-0.737246`
- kl_mean: `65795.584704`
- eta_mean: `3.091360`

### Train episode 5

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `637.764051`
- pi_loss_mean: `-0.867047`
- kl_mean: `204543.524671`
- eta_mean: `3.214644`

### Eval episode 1

- episode_return: `-262582.304842`
- steps: `2903`

### Eval episode 2

- episode_return: `-262582.304842`
- steps: `2903`

