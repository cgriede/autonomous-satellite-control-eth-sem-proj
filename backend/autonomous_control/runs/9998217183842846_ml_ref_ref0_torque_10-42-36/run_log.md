# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `agent reference ref0`
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
- created_utc: `2026-06-30T10:42:37.154261+00:00`

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

- episode_return: `-76.183724`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `55.394754`
- pi_loss_mean: `-10.031052`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-31.061850`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `172.187161`
- pi_loss_mean: `-25.361619`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-8.782254`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `344.507975`
- pi_loss_mean: `-39.370291`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-52.759298`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `462.599622`
- pi_loss_mean: `-51.039259`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-18.067198`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `843.184206`
- pi_loss_mean: `-63.695876`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-40.467200`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1716.225020`
- pi_loss_mean: `-80.101225`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-32.929376`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2076.471045`
- pi_loss_mean: `-96.446853`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-35.094807`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1803.235044`
- pi_loss_mean: `-108.200852`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-38.305556`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1870.212349`
- pi_loss_mean: `-119.116415`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-70.542057`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1886.603557`
- pi_loss_mean: `-122.659087`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-73.137848`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1925.436060`
- pi_loss_mean: `-121.372790`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-69.881267`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2054.040421`
- pi_loss_mean: `-119.604449`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-71.716074`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2108.514046`
- pi_loss_mean: `-119.358174`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-71.536125`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2019.692791`
- pi_loss_mean: `-115.936328`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-73.809135`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2432.736619`
- pi_loss_mean: `-112.192792`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-74.953495`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2584.905727`
- pi_loss_mean: `-108.430351`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-71.605411`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2061.148225`
- pi_loss_mean: `-106.263994`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-68.993373`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2616.763281`
- pi_loss_mean: `-101.755172`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-69.332619`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2382.443556`
- pi_loss_mean: `-98.134003`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-71.220082`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2796.437650`
- pi_loss_mean: `-88.710112`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-69.454625`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2851.528508`
- pi_loss_mean: `-89.874445`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-70.911404`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2515.730737`
- pi_loss_mean: `-85.471273`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-73.287346`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3136.196752`
- pi_loss_mean: `-78.457329`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-72.435912`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3728.314862`
- pi_loss_mean: `-73.430319`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-75.739836`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2615.404378`
- pi_loss_mean: `-71.452582`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-72.161337`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6327.018549`
- pi_loss_mean: `-73.361377`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-73.997997`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10035.823770`
- pi_loss_mean: `-75.394920`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-50.009211`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6848.470672`
- pi_loss_mean: `-74.596545`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-31.311944`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4822.752018`
- pi_loss_mean: `-69.866054`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-50.077303`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5887.390107`
- pi_loss_mean: `-68.392619`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-75.151167`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5012.544485`
- pi_loss_mean: `-61.488968`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-75.550080`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3659.528967`
- pi_loss_mean: `-52.859920`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-72.765169`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3427.623829`
- pi_loss_mean: `-47.180547`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-73.756057`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2942.976217`
- pi_loss_mean: `-40.285853`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-74.512354`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2395.916682`
- pi_loss_mean: `-33.866587`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-75.879985`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2245.529093`
- pi_loss_mean: `-29.597575`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-73.988593`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1813.588613`
- pi_loss_mean: `-25.536629`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-76.327264`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1696.351355`
- pi_loss_mean: `-23.307834`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-73.599782`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1763.480585`
- pi_loss_mean: `-20.231317`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-55.568075`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1665.473559`
- pi_loss_mean: `-19.752926`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-43.687332`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1708.668294`
- pi_loss_mean: `-19.025822`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-43.989693`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1502.189872`
- pi_loss_mean: `-17.425271`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-49.958863`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1220.881814`
- pi_loss_mean: `-15.191745`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-36.351971`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1320.759539`
- pi_loss_mean: `-11.630891`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-68.977031`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1152.201431`
- pi_loss_mean: `-11.519452`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-70.814272`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1154.626717`
- pi_loss_mean: `-9.260139`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-70.504484`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `986.773938`
- pi_loss_mean: `-5.974726`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-72.293322`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `925.471777`
- pi_loss_mean: `-2.556120`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-70.647168`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1027.219883`
- pi_loss_mean: `-0.237234`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `8.366751`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1011.197412`
- pi_loss_mean: `-0.204225`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-11.128068`
- steps: `516`

### Eval episode 2

- episode_return: `-11.128068`
- steps: `516`

