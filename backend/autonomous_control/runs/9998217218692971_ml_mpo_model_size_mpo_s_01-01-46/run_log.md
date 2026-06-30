# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo model size`
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
- created_utc: `2026-06-30T01:01:47.030108+00:00`

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

- episode_return: `-101.300828`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `28.692377`
- pi_loss_mean: `-0.838152`
- kl_mean: `158.523453`
- eta_mean: `2.944671`

### Train episode 2

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.900565`
- pi_loss_mean: `-0.869821`
- kl_mean: `-0.000001`
- eta_mean: `2.966781`

### Train episode 3

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.510105`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `2.966260`

### Train episode 4

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.232955`
- pi_loss_mean: `-0.869813`
- kl_mean: `-0.000001`
- eta_mean: `2.965516`

### Train episode 5

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.123832`
- pi_loss_mean: `-0.869839`
- kl_mean: `-0.000001`
- eta_mean: `2.964500`

### Train episode 6

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.186138`
- pi_loss_mean: `-0.869829`
- kl_mean: `-0.000001`
- eta_mean: `2.963150`

### Train episode 7

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.514794`
- pi_loss_mean: `-0.869836`
- kl_mean: `-0.000001`
- eta_mean: `2.961373`

### Train episode 8

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.090925`
- pi_loss_mean: `-0.869827`
- kl_mean: `-0.000001`
- eta_mean: `2.959055`

### Train episode 9

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.062297`
- pi_loss_mean: `-0.869818`
- kl_mean: `-0.000001`
- eta_mean: `2.956044`

### Train episode 10

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.128660`
- pi_loss_mean: `-0.869826`
- kl_mean: `-0.000001`
- eta_mean: `2.952142`

### Train episode 11

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.108180`
- pi_loss_mean: `-0.869832`
- kl_mean: `-0.000001`
- eta_mean: `2.947096`

### Train episode 12

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.130463`
- pi_loss_mean: `-0.869816`
- kl_mean: `-0.000001`
- eta_mean: `2.940581`

### Train episode 13

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.194262`
- pi_loss_mean: `-0.869836`
- kl_mean: `-0.000001`
- eta_mean: `2.932186`

### Train episode 14

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.620820`
- pi_loss_mean: `-0.869835`
- kl_mean: `-0.000001`
- eta_mean: `2.921385`

### Train episode 15

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.051554`
- pi_loss_mean: `-0.869837`
- kl_mean: `-0.000001`
- eta_mean: `2.907517`

### Train episode 16

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.115895`
- pi_loss_mean: `-0.869817`
- kl_mean: `-0.000001`
- eta_mean: `2.889759`

### Train episode 17

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.151824`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `2.867090`

### Train episode 18

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.238083`
- pi_loss_mean: `-0.869821`
- kl_mean: `-0.000001`
- eta_mean: `2.838271`

### Train episode 19

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.063202`
- pi_loss_mean: `-0.869825`
- kl_mean: `-0.000001`
- eta_mean: `2.801817`

### Train episode 20

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.104400`
- pi_loss_mean: `-0.869827`
- kl_mean: `-0.000001`
- eta_mean: `2.756010`

### Train episode 21

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.076666`
- pi_loss_mean: `-0.869834`
- kl_mean: `-0.000001`
- eta_mean: `2.698915`

### Train episode 22

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.086317`
- pi_loss_mean: `-0.869813`
- kl_mean: `-0.000001`
- eta_mean: `2.628472`

### Train episode 23

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.164758`
- pi_loss_mean: `-0.869834`
- kl_mean: `-0.000001`
- eta_mean: `2.542650`

### Train episode 24

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.145280`
- pi_loss_mean: `-0.869823`
- kl_mean: `-0.000001`
- eta_mean: `2.439689`

### Train episode 25

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.061590`
- pi_loss_mean: `-0.869841`
- kl_mean: `-0.000001`
- eta_mean: `2.318433`

### Train episode 26

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.068707`
- pi_loss_mean: `-0.869822`
- kl_mean: `-0.000001`
- eta_mean: `2.178723`

### Train episode 27

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.156133`
- pi_loss_mean: `-0.869835`
- kl_mean: `-0.000001`
- eta_mean: `2.021763`

### Train episode 28

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.226611`
- pi_loss_mean: `-0.869815`
- kl_mean: `-0.000001`
- eta_mean: `1.850352`

### Train episode 29

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.085214`
- pi_loss_mean: `-0.869822`
- kl_mean: `-0.000001`
- eta_mean: `1.668856`

### Train episode 30

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.070684`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `1.482830`

### Train episode 31

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.105607`
- pi_loss_mean: `-0.869834`
- kl_mean: `-0.000001`
- eta_mean: `1.298344`

### Train episode 32

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.066169`
- pi_loss_mean: `-0.869819`
- kl_mean: `-0.000001`
- eta_mean: `1.121171`

### Train episode 33

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.069821`
- pi_loss_mean: `-0.869803`
- kl_mean: `-0.000001`
- eta_mean: `0.956070`

### Train episode 34

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.074320`
- pi_loss_mean: `-0.869841`
- kl_mean: `-0.000001`
- eta_mean: `0.806343`

### Train episode 35

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.193870`
- pi_loss_mean: `-0.869816`
- kl_mean: `-0.000001`
- eta_mean: `0.673735`

### Train episode 36

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.062398`
- pi_loss_mean: `-0.869832`
- kl_mean: `-0.000001`
- eta_mean: `0.558612`

### Train episode 37

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.070516`
- pi_loss_mean: `-0.869828`
- kl_mean: `-0.000001`
- eta_mean: `0.460295`

### Train episode 38

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.069353`
- pi_loss_mean: `-0.869808`
- kl_mean: `-0.000001`
- eta_mean: `0.377427`

### Train episode 39

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.111968`
- pi_loss_mean: `-0.869846`
- kl_mean: `-0.000001`
- eta_mean: `0.308300`

### Train episode 40

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.116700`
- pi_loss_mean: `-0.869818`
- kl_mean: `-0.000001`
- eta_mean: `0.251099`

### Train episode 41

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.121333`
- pi_loss_mean: `-0.869846`
- kl_mean: `-0.000001`
- eta_mean: `0.204056`

### Train episode 42

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.069733`
- pi_loss_mean: `-0.869842`
- kl_mean: `-0.000001`
- eta_mean: `0.165549`

### Train episode 43

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.051490`
- pi_loss_mean: `-0.869860`
- kl_mean: `-0.000001`
- eta_mean: `0.134138`

### Train episode 44

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.062093`
- pi_loss_mean: `-0.869840`
- kl_mean: `-0.000001`
- eta_mean: `0.108585`

### Train episode 45

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.074923`
- pi_loss_mean: `-0.869829`
- kl_mean: `-0.000001`
- eta_mean: `0.087838`

### Train episode 46

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.221612`
- pi_loss_mean: `-0.869828`
- kl_mean: `-0.000001`
- eta_mean: `0.071018`

### Train episode 47

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.087896`
- pi_loss_mean: `-0.869843`
- kl_mean: `-0.000001`
- eta_mean: `0.057397`

### Train episode 48

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.054881`
- pi_loss_mean: `-0.869840`
- kl_mean: `-0.000001`
- eta_mean: `0.046374`

### Train episode 49

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.079928`
- pi_loss_mean: `-0.869832`
- kl_mean: `-0.000001`
- eta_mean: `0.037461`

### Train episode 50

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.073490`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `0.030256`

### Eval episode 1

- episode_return: `-51.600000`
- steps: `516`

### Eval episode 2

- episode_return: `-51.600000`
- steps: `516`

