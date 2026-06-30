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
- created_utc: `2026-06-30T02:44:38.138590+00:00`

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

- episode_return: `-75.675695`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `55.442084`
- pi_loss_mean: `-10.096917`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-5.585347`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `179.757979`
- pi_loss_mean: `-25.349007`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `0.474323`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `367.641785`
- pi_loss_mean: `-39.884995`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `8.231915`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `459.153385`
- pi_loss_mean: `-52.186601`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-9.452697`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `566.568070`
- pi_loss_mean: `-63.484671`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-22.796907`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `859.489956`
- pi_loss_mean: `-73.370288`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-40.608495`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2249.326535`
- pi_loss_mean: `-92.866459`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-43.684821`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2507.212945`
- pi_loss_mean: `-115.219582`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-38.181873`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2375.801222`
- pi_loss_mean: `-127.780154`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-34.920136`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2321.062130`
- pi_loss_mean: `-133.310493`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-32.946769`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2334.883788`
- pi_loss_mean: `-137.632611`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-80.148962`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1677.002816`
- pi_loss_mean: `-135.876727`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-80.260786`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1648.127554`
- pi_loss_mean: `-130.400839`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-78.374619`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1499.748685`
- pi_loss_mean: `-128.017976`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-33.734922`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1702.348503`
- pi_loss_mean: `-127.194152`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-70.901880`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1574.815973`
- pi_loss_mean: `-120.765241`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-70.471611`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1352.225620`
- pi_loss_mean: `-110.525481`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-73.452789`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2173.296561`
- pi_loss_mean: `-99.822402`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-72.450923`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1173.823754`
- pi_loss_mean: `-92.846383`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-72.498441`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1918.118221`
- pi_loss_mean: `-81.796576`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-74.136667`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2160.948485`
- pi_loss_mean: `-74.619522`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-70.491882`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1842.613537`
- pi_loss_mean: `-67.063245`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-71.220377`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1364.581417`
- pi_loss_mean: `-60.062205`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-71.462080`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2224.377940`
- pi_loss_mean: `-51.004706`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-71.744545`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1181.632534`
- pi_loss_mean: `-44.896585`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-43.969797`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1100.073011`
- pi_loss_mean: `-39.499136`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-28.397981`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2267.135420`
- pi_loss_mean: `-35.011026`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-71.139860`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1462.140798`
- pi_loss_mean: `-28.945452`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-74.225093`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1369.251057`
- pi_loss_mean: `-23.721702`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-74.392754`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1494.092439`
- pi_loss_mean: `-17.420685`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-71.561273`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `800.234797`
- pi_loss_mean: `-13.132617`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-70.686891`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `744.964533`
- pi_loss_mean: `-9.094808`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-70.906304`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `512.130213`
- pi_loss_mean: `-5.912930`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-18.008214`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1529.230099`
- pi_loss_mean: `-2.030051`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-73.763387`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `574.570410`
- pi_loss_mean: `0.937484`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-71.074443`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `541.688941`
- pi_loss_mean: `3.267602`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-70.958800`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `352.594543`
- pi_loss_mean: `5.340008`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-70.297349`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `235.834525`
- pi_loss_mean: `6.723783`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `11.191824`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `297.764690`
- pi_loss_mean: `7.266323`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-67.991966`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `365.622944`
- pi_loss_mean: `10.538362`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-68.199545`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `106.407345`
- pi_loss_mean: `12.356912`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-68.425941`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `99.844534`
- pi_loss_mean: `12.759043`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-68.538277`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `98.523659`
- pi_loss_mean: `13.529776`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-46.053015`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `200.269774`
- pi_loss_mean: `13.799543`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-69.022993`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `113.392074`
- pi_loss_mean: `12.886825`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-53.256336`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `94.040689`
- pi_loss_mean: `12.277011`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-4.099284`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `93.599577`
- pi_loss_mean: `12.855022`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-43.043203`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `115.017825`
- pi_loss_mean: `12.360766`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-36.195102`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `79.088409`
- pi_loss_mean: `12.292868`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `9.591824`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `61.294872`
- pi_loss_mean: `12.422335`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-3.910672`
- steps: `516`

### Eval episode 2

- episode_return: `-3.910672`
- steps: `516`

