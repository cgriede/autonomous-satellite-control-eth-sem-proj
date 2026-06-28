# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `5`
- train_episodes: `10`
- eval_episodes: `2`
- scalar_dim: `55`
- vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- vision_seq_lens: `[100, 200]`
- encoder_output_dim: `180`
- code_embed_dim: `8`
- cnn_embedding_dim: `32`
- num_cnn_layers: `2`
- feature_attitude_keys: `['body_z_angle_rad', 'omega_sat_rad_s']`
- feature_orbit_keys: `['theta_orbit_rad', 'primary_camera_image_quality']`
- feature_vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- sampled_altitude_km: `528.7583065070219`
- created_utc: `2026-06-27T13:50:06.689594+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `145.371624`
- steps: `1935`

### Warmup episode 2 (baseline overflight)

- episode_return: `108.177431`
- steps: `1935`

### Warmup episode 3 (baseline overflight)

- episode_return: `95.073452`
- steps: `1935`

### Warmup episode 4 (baseline overflight)

- episode_return: `46.562585`
- steps: `1935`

### Warmup episode 5 (baseline overflight)

- episode_return: `50.638123`
- steps: `1935`

### Train episode 1

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `4.270803`
- pi_loss_mean: `-0.848115`
- kl_mean: `169352.549383`
- eta_mean: `20.933787`

### Train episode 2

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.366964`
- pi_loss_mean: `-0.869831`
- kl_mean: `230361.468056`
- eta_mean: `1343.749719`

### Train episode 3

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.175566`
- pi_loss_mean: `-0.869827`
- kl_mean: `270060.128246`
- eta_mean: `122768.728909`

### Train episode 4

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.153785`
- pi_loss_mean: `-0.869823`
- kl_mean: `298855.695066`
- eta_mean: `11399970.467345`

### Train episode 5

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.124408`
- pi_loss_mean: `-0.869823`
- kl_mean: `335055.833043`
- eta_mean: `1093965724.613954`

### Train episode 6

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.077665`
- pi_loss_mean: `-0.869832`
- kl_mean: `378212.207865`
- eta_mean: `102797121923.902847`

### Train episode 7

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.033738`
- pi_loss_mean: `-0.869836`
- kl_mean: `384617.274645`
- eta_mean: `9167263853302.871094`

### Train episode 8

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.110069`
- pi_loss_mean: `-0.869820`
- kl_mean: `417756.130329`
- eta_mean: `103524595834088.312500`

### Train episode 9

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.040196`
- pi_loss_mean: `-0.869823`
- kl_mean: `481446.013307`
- eta_mean: `112673836498944.000000`

### Train episode 10

- episode_return: `0.000000`
- steps: `1935`
- n_train_updates: `1935`
- q_loss_mean: `0.062841`
- pi_loss_mean: `-0.869830`
- kl_mean: `482824.891667`
- eta_mean: `112673836498944.000000`

### Eval episode 1

- episode_return: `0.000000`
- steps: `1935`

### Eval episode 2

- episode_return: `0.000000`
- steps: `1935`

