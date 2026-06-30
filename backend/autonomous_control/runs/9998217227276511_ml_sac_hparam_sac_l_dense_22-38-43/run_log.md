# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `sac hparam grid`
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
- created_utc: `2026-06-29T22:38:43.489406+00:00`

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

- episode_return: `-73.110731`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `51.238555`
- pi_loss_mean: `-11.592310`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-0.477792`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `52.628685`
- pi_loss_mean: `-18.077738`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-70.968841`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `79.944241`
- pi_loss_mean: `-26.562683`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-33.272571`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `182.756801`
- pi_loss_mean: `-34.955086`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-68.021732`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `408.351435`
- pi_loss_mean: `-48.213305`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-70.366694`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `510.988602`
- pi_loss_mean: `-57.301859`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-43.748122`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `773.965206`
- pi_loss_mean: `-68.923013`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-60.229605`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `513.049449`
- pi_loss_mean: `-80.049297`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-72.307657`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `878.107977`
- pi_loss_mean: `-88.730624`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-60.358657`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `665.889301`
- pi_loss_mean: `-93.886122`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-71.595103`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `794.701115`
- pi_loss_mean: `-93.792132`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-75.183678`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1314.580512`
- pi_loss_mean: `-95.526310`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-59.460706`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `811.031154`
- pi_loss_mean: `-99.885693`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-20.320764`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1277.691894`
- pi_loss_mean: `-103.721296`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-0.297479`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1245.183201`
- pi_loss_mean: `-109.566623`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-36.266058`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1494.125800`
- pi_loss_mean: `-109.863856`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-42.811191`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `709.219393`
- pi_loss_mean: `-108.984809`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-71.238255`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `836.630153`
- pi_loss_mean: `-103.914247`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-74.174677`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `631.447299`
- pi_loss_mean: `-99.371635`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-71.797718`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1276.794423`
- pi_loss_mean: `-91.630705`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-47.929927`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `982.752344`
- pi_loss_mean: `-90.687644`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-70.803571`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1126.970361`
- pi_loss_mean: `-86.961354`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-71.567035`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1008.674277`
- pi_loss_mean: `-83.210138`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-51.740210`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `927.179037`
- pi_loss_mean: `-80.761632`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-12.895296`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1054.151159`
- pi_loss_mean: `-80.641376`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-55.895448`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `441.943340`
- pi_loss_mean: `-81.313263`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `9.076122`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `737.318240`
- pi_loss_mean: `-79.215846`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-27.674157`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1262.651013`
- pi_loss_mean: `-79.313975`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-6.137870`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `530.285225`
- pi_loss_mean: `-82.104590`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-39.928825`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1510.822916`
- pi_loss_mean: `-80.497870`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-69.622972`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `475.970909`
- pi_loss_mean: `-79.058752`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-70.714979`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `734.805046`
- pi_loss_mean: `-75.929832`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-47.801594`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `819.204488`
- pi_loss_mean: `-72.461397`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-51.389807`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1614.189966`
- pi_loss_mean: `-67.054574`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-70.090875`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `963.443920`
- pi_loss_mean: `-64.142911`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-69.381410`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `927.234019`
- pi_loss_mean: `-61.917653`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-24.960536`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `585.829779`
- pi_loss_mean: `-60.696007`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-2.070585`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1558.817102`
- pi_loss_mean: `-58.144299`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-69.441456`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `727.821877`
- pi_loss_mean: `-57.394016`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-30.832777`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1130.914822`
- pi_loss_mean: `-55.811184`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-32.137416`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1880.600807`
- pi_loss_mean: `-53.962297`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `10.292870`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1370.079828`
- pi_loss_mean: `-53.252913`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-32.224152`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1030.247549`
- pi_loss_mean: `-52.789075`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-18.416206`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `492.037408`
- pi_loss_mean: `-50.670800`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-69.758329`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `377.458672`
- pi_loss_mean: `-49.286010`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-45.555310`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `422.329309`
- pi_loss_mean: `-47.344775`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-68.372065`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `424.889899`
- pi_loss_mean: `-44.353302`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-37.496355`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `484.551684`
- pi_loss_mean: `-41.046312`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-69.330205`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `367.986675`
- pi_loss_mean: `-39.373882`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `-69.443263`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `219.268805`
- pi_loss_mean: `-37.939913`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `24.269154`
- steps: `516`

### Eval episode 2

- episode_return: `24.269154`
- steps: `516`

