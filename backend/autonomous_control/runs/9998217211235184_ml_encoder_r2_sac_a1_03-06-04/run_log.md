# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `modular encoder r2`
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
- created_utc: `2026-06-30T03:06:04.816293+00:00`

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

- episode_return: `-78.985044`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `48.190215`
- pi_loss_mean: `-8.949315`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-4.342051`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `146.707949`
- pi_loss_mean: `-25.972642`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `12.930375`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `326.935022`
- pi_loss_mean: `-43.348646`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-36.742578`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `555.985357`
- pi_loss_mean: `-60.675655`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-55.321994`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `848.923849`
- pi_loss_mean: `-79.968338`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-63.677928`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1462.403782`
- pi_loss_mean: `-101.006630`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-49.611829`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6962.436773`
- pi_loss_mean: `-133.106474`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-40.105991`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `9135.525912`
- pi_loss_mean: `-168.650548`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-78.390658`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7650.691142`
- pi_loss_mean: `-186.078763`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-27.947205`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `9070.012532`
- pi_loss_mean: `-199.412700`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-19.542035`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `12849.651007`
- pi_loss_mean: `-221.735124`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-74.465106`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10964.277446`
- pi_loss_mean: `-225.094044`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-27.273035`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `18715.481379`
- pi_loss_mean: `-225.341504`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-68.411134`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `14294.624616`
- pi_loss_mean: `-219.362988`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-9.673324`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `14396.951594`
- pi_loss_mean: `-217.464260`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-17.281406`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `13072.166691`
- pi_loss_mean: `-219.576726`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-68.766206`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10488.130610`
- pi_loss_mean: `-202.452093`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-67.806645`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8201.879952`
- pi_loss_mean: `-185.485792`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-63.282186`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `9324.204729`
- pi_loss_mean: `-167.183783`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-65.116686`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7301.959613`
- pi_loss_mean: `-153.572668`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-64.443087`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6051.392462`
- pi_loss_mean: `-144.684892`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-64.640518`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5368.955143`
- pi_loss_mean: `-134.018746`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-69.924301`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4284.405670`
- pi_loss_mean: `-125.190600`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `16.984925`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4376.253256`
- pi_loss_mean: `-121.386108`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-7.509493`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4653.816748`
- pi_loss_mean: `-125.761817`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-38.747303`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3693.567529`
- pi_loss_mean: `-130.752902`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-37.084746`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3176.165802`
- pi_loss_mean: `-127.741613`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-55.323102`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3034.248309`
- pi_loss_mean: `-120.427689`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-79.953250`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2323.544562`
- pi_loss_mean: `-112.896345`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `41.071979`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2150.011106`
- pi_loss_mean: `-105.023733`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `83.793611`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2047.776202`
- pi_loss_mean: `-100.876983`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-5.007244`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1726.245642`
- pi_loss_mean: `-93.806936`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `27.756444`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2061.527565`
- pi_loss_mean: `-94.590307`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `31.952956`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1858.854971`
- pi_loss_mean: `-95.175220`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `86.163264`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1807.610811`
- pi_loss_mean: `-95.672720`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `104.810218`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1784.207010`
- pi_loss_mean: `-93.258994`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `106.370677`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1661.738494`
- pi_loss_mean: `-91.588644`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-6.805857`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1469.736392`
- pi_loss_mean: `-87.953820`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `65.372174`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1570.704151`
- pi_loss_mean: `-86.477907`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `87.739597`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1532.249236`
- pi_loss_mean: `-87.880047`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `25.414271`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1260.767334`
- pi_loss_mean: `-86.286255`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `137.165388`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1180.925163`
- pi_loss_mean: `-91.010162`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `126.774054`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1200.878816`
- pi_loss_mean: `-91.648728`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `62.880645`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1400.807641`
- pi_loss_mean: `-92.146019`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `62.194521`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1026.942697`
- pi_loss_mean: `-91.366962`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `58.854636`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1071.410664`
- pi_loss_mean: `-88.940100`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `104.370703`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `949.601735`
- pi_loss_mean: `-87.598088`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `121.012382`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `870.809648`
- pi_loss_mean: `-87.137804`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `4.552300`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `825.149193`
- pi_loss_mean: `-81.805608`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `39.254105`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `851.989349`
- pi_loss_mean: `-81.748498`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `80.913264`
- steps: `516`

### Eval episode 2

- episode_return: `80.913264`
- steps: `516`

