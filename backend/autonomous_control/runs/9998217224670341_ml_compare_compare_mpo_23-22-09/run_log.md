# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `compare compare mpo`
- warmup_episodes: `5`
- train_episodes: `50`
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
- created_utc: `2026-06-29T23:22:09.659037+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `467.881585`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `397.468337`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `253.995889`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `406.677421`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `439.915993`
- steps: `516`

### Train episode 1

- episode_return: `-100.540380`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `52.985005`
- pi_loss_mean: `-0.784078`
- kl_mean: `111254.366325`
- eta_mean: `4.290338`

### Train episode 2

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.077938`
- pi_loss_mean: `-0.869812`
- kl_mean: `160459.612009`
- eta_mean: `9.507314`

### Train episode 3

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.289091`
- pi_loss_mean: `-0.869830`
- kl_mean: `175700.766957`
- eta_mean: `23.065513`

### Train episode 4

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.857330`
- pi_loss_mean: `-0.869826`
- kl_mean: `191647.015413`
- eta_mean: `63.502915`

### Train episode 5

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.220006`
- pi_loss_mean: `-0.869835`
- kl_mean: `202062.768320`
- eta_mean: `189.531393`

### Train episode 6

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.879864`
- pi_loss_mean: `-0.869803`
- kl_mean: `211128.637355`
- eta_mean: `593.668745`

### Train episode 7

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.641462`
- pi_loss_mean: `-0.869845`
- kl_mean: `219880.720355`
- eta_mean: `1912.955467`

### Train episode 8

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.553435`
- pi_loss_mean: `-0.869817`
- kl_mean: `225267.652313`
- eta_mean: `6250.488590`

### Train episode 9

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.469431`
- pi_loss_mean: `-0.869851`
- kl_mean: `233786.102774`
- eta_mean: `20660.270883`

### Train episode 10

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.354977`
- pi_loss_mean: `-0.869835`
- kl_mean: `246977.391443`
- eta_mean: `69640.124712`

### Train episode 11

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.339170`
- pi_loss_mean: `-0.869835`
- kl_mean: `254223.282613`
- eta_mean: `234227.731604`

### Train episode 12

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.255177`
- pi_loss_mean: `-0.869837`
- kl_mean: `257054.695010`
- eta_mean: `780215.921391`

### Train episode 13

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.222438`
- pi_loss_mean: `-0.869833`
- kl_mean: `268059.422935`
- eta_mean: `2610526.354409`

### Train episode 14

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.215280`
- pi_loss_mean: `-0.869829`
- kl_mean: `287229.188227`
- eta_mean: `8960538.393411`

### Train episode 15

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.174481`
- pi_loss_mean: `-0.869811`
- kl_mean: `294621.677598`
- eta_mean: `30285141.100775`

### Train episode 16

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.139969`
- pi_loss_mean: `-0.869825`
- kl_mean: `293727.999788`
- eta_mean: `100693906.201550`

### Train episode 17

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.199690`
- pi_loss_mean: `-0.869826`
- kl_mean: `313782.455154`
- eta_mean: `339721725.798450`

### Train episode 18

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.111848`
- pi_loss_mean: `-0.869842`
- kl_mean: `325227.284278`
- eta_mean: `1159826401.860465`

### Train episode 19

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.131681`
- pi_loss_mean: `-0.869838`
- kl_mean: `340973.754512`
- eta_mean: `3917578755.224806`

### Train episode 20

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.170522`
- pi_loss_mean: `-0.869821`
- kl_mean: `366948.641109`
- eta_mean: `13459516357.457365`

### Train episode 21

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.131538`
- pi_loss_mean: `-0.869822`
- kl_mean: `379515.693920`
- eta_mean: `45968963135.503876`

### Train episode 22

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.108969`
- pi_loss_mean: `-0.869835`
- kl_mean: `378877.326369`
- eta_mean: `152709836863.503876`

### Eval episode 1

- episode_return: `-51.600000`
- steps: `516`

### Eval episode 2

- episode_return: `-51.600000`
- steps: `516`

