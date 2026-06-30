# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo decoupled dual torque`
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
- created_utc: `2026-06-30T16:05:19.825910+00:00`

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

- episode_return: `-808.296730`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `34.854300`
- pi_loss_mean: `-0.172827`
- kl_mean: `-0.116730`
- eta_mean: `3.209877`

### Train episode 2

- episode_return: `-829.749872`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `53.480301`
- pi_loss_mean: `-0.240421`
- kl_mean: `-0.060895`
- eta_mean: `5.283766`

### Train episode 3

- episode_return: `-546.706172`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `112.113198`
- pi_loss_mean: `-0.303109`
- kl_mean: `0.002441`
- eta_mean: `6.775056`

### Train episode 4

- episode_return: `-251.309363`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `176.590124`
- pi_loss_mean: `-0.340868`
- kl_mean: `0.034550`
- eta_mean: `5.631056`

### Train episode 5

- episode_return: `-139.420159`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `260.839863`
- pi_loss_mean: `-0.380848`
- kl_mean: `0.029847`
- eta_mean: `4.294747`

### Train episode 6

- episode_return: `-92.917480`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `351.667524`
- pi_loss_mean: `-0.412312`
- kl_mean: `0.023379`
- eta_mean: `3.328473`

### Train episode 7

- episode_return: `-12.535585`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `560.628721`
- pi_loss_mean: `-0.438850`
- kl_mean: `0.022628`
- eta_mean: `2.595753`

### Train episode 8

- episode_return: `-40.681518`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `723.504345`
- pi_loss_mean: `-0.459555`
- kl_mean: `0.020546`
- eta_mean: `2.046705`

### Train episode 9

- episode_return: `-33.866435`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1131.241775`
- pi_loss_mean: `-0.471902`
- kl_mean: `0.016270`
- eta_mean: `1.676639`

### Train episode 10

- episode_return: `-46.247096`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1721.414262`
- pi_loss_mean: `-0.476949`
- kl_mean: `0.014175`
- eta_mean: `1.477141`

### Train episode 11

- episode_return: `-32.802319`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2185.194722`
- pi_loss_mean: `-0.478306`
- kl_mean: `0.014525`
- eta_mean: `1.708628`

### Train episode 12

- episode_return: `-6.674390`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2051.753071`
- pi_loss_mean: `-0.482904`
- kl_mean: `0.015253`
- eta_mean: `2.218103`

### Train episode 13

- episode_return: `-60.942636`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1841.726267`
- pi_loss_mean: `-0.486281`
- kl_mean: `0.017407`
- eta_mean: `2.645244`

### Train episode 14

- episode_return: `-50.995544`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1680.936278`
- pi_loss_mean: `-0.488231`
- kl_mean: `0.018705`
- eta_mean: `3.490602`

### Train episode 15

- episode_return: `-50.736652`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2195.867294`
- pi_loss_mean: `-0.494327`
- kl_mean: `0.013140`
- eta_mean: `3.529801`

### Train episode 16

- episode_return: `-50.673652`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1754.953318`
- pi_loss_mean: `-0.498664`
- kl_mean: `0.010767`
- eta_mean: `2.751155`

### Train episode 17

- episode_return: `-51.207512`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1553.934423`
- pi_loss_mean: `-0.500786`
- kl_mean: `0.011905`
- eta_mean: `2.233507`

### Train episode 18

- episode_return: `-49.033916`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1610.209603`
- pi_loss_mean: `-0.498662`
- kl_mean: `0.020626`
- eta_mean: `2.062734`

### Train episode 19

- episode_return: `-55.803431`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1526.577533`
- pi_loss_mean: `-0.483430`
- kl_mean: `0.058397`
- eta_mean: `3.646204`

### Train episode 20

- episode_return: `-55.406542`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2106.125551`
- pi_loss_mean: `-0.492991`
- kl_mean: `0.017882`
- eta_mean: `4.238805`

### Train episode 21

- episode_return: `-53.302982`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2935.857028`
- pi_loss_mean: `-0.494240`
- kl_mean: `0.016065`
- eta_mean: `3.724828`

### Train episode 22

- episode_return: `-51.642775`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2798.726226`
- pi_loss_mean: `-0.494103`
- kl_mean: `0.018280`
- eta_mean: `3.428259`

### Train episode 23

- episode_return: `-42.824363`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2887.461674`
- pi_loss_mean: `-0.494588`
- kl_mean: `0.018072`
- eta_mean: `2.978924`

### Train episode 24

- episode_return: `-58.892597`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1598.332569`
- pi_loss_mean: `-0.494316`
- kl_mean: `0.018149`
- eta_mean: `2.743864`

### Train episode 25

- episode_return: `-36.088752`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1249.942786`
- pi_loss_mean: `-0.494513`
- kl_mean: `0.021838`
- eta_mean: `2.391851`

### Train episode 26

- episode_return: `-28.649829`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2429.318925`
- pi_loss_mean: `-0.494096`
- kl_mean: `0.018867`
- eta_mean: `2.227971`

### Train episode 27

- episode_return: `-56.300406`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1577.740564`
- pi_loss_mean: `-0.491801`
- kl_mean: `0.021784`
- eta_mean: `2.257001`

### Train episode 28

- episode_return: `-62.293636`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5569.325679`
- pi_loss_mean: `-0.489219`
- kl_mean: `0.021897`
- eta_mean: `2.643578`

### Train episode 29

- episode_return: `8.699291`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1747.248364`
- pi_loss_mean: `-0.489392`
- kl_mean: `0.020416`
- eta_mean: `2.748264`

### Train episode 30

- episode_return: `-68.251903`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2022.832760`
- pi_loss_mean: `-0.490328`
- kl_mean: `0.018685`
- eta_mean: `2.480145`

### Train episode 31

- episode_return: `-56.195406`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1432.425197`
- pi_loss_mean: `-0.491892`
- kl_mean: `0.019056`
- eta_mean: `2.106976`

### Train episode 32

- episode_return: `-46.740417`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1090.022322`
- pi_loss_mean: `-0.491786`
- kl_mean: `0.019953`
- eta_mean: `1.822874`

### Train episode 33

- episode_return: `-58.952010`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1060.287408`
- pi_loss_mean: `-0.491679`
- kl_mean: `0.019643`
- eta_mean: `1.685989`

### Train episode 34

- episode_return: `-30.570901`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1118.544089`
- pi_loss_mean: `-0.490730`
- kl_mean: `0.020246`
- eta_mean: `1.668100`

### Train episode 35

- episode_return: `-48.825140`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1722.309021`
- pi_loss_mean: `-0.489117`
- kl_mean: `0.021271`
- eta_mean: `1.758285`

### Train episode 36

- episode_return: `-83.431590`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `838.253324`
- pi_loss_mean: `-0.489458`
- kl_mean: `0.019399`
- eta_mean: `1.737691`

### Train episode 37

- episode_return: `-88.227498`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `511.503207`
- pi_loss_mean: `-0.488639`
- kl_mean: `0.021351`
- eta_mean: `1.686033`

### Train episode 38

- episode_return: `-62.966926`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `531.629185`
- pi_loss_mean: `-0.487811`
- kl_mean: `0.021493`
- eta_mean: `1.627304`

### Train episode 39

- episode_return: `-51.368846`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `532.733623`
- pi_loss_mean: `-0.488834`
- kl_mean: `0.018803`
- eta_mean: `1.540107`

### Train episode 40

- episode_return: `-80.809557`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1317.712181`
- pi_loss_mean: `-0.489121`
- kl_mean: `0.019374`
- eta_mean: `1.430543`

### Train episode 41

- episode_return: `-85.748480`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `795.851865`
- pi_loss_mean: `-0.490302`
- kl_mean: `0.019804`
- eta_mean: `1.329677`

### Train episode 42

- episode_return: `-84.556818`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `737.135152`
- pi_loss_mean: `-0.490359`
- kl_mean: `0.019877`
- eta_mean: `1.222331`

### Train episode 43

- episode_return: `-85.993702`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `732.217209`
- pi_loss_mean: `-0.490325`
- kl_mean: `0.019702`
- eta_mean: `1.153391`

### Train episode 44

- episode_return: `-74.197979`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `485.002735`
- pi_loss_mean: `-0.489643`
- kl_mean: `0.020491`
- eta_mean: `1.097298`

### Train episode 45

- episode_return: `-80.412403`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `303.132726`
- pi_loss_mean: `-0.490324`
- kl_mean: `0.019079`
- eta_mean: `1.012964`

### Train episode 46

- episode_return: `-69.702963`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `169.111071`
- pi_loss_mean: `-0.490135`
- kl_mean: `0.019741`
- eta_mean: `0.901230`

### Train episode 47

- episode_return: `-80.461446`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `177.427626`
- pi_loss_mean: `-0.490519`
- kl_mean: `0.019727`
- eta_mean: `0.841676`

### Train episode 48

- episode_return: `-76.347311`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `102.740528`
- pi_loss_mean: `-0.490943`
- kl_mean: `0.018800`
- eta_mean: `0.789046`

### Train episode 49

- episode_return: `-50.402003`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `98.469280`
- pi_loss_mean: `-0.490581`
- kl_mean: `0.020284`
- eta_mean: `0.777634`

### Train episode 50

- episode_return: `-76.526380`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `85.678399`
- pi_loss_mean: `-0.491294`
- kl_mean: `0.020708`
- eta_mean: `0.787820`

### Eval episode 1

- episode_return: `-81.079085`
- steps: `516`

### Eval episode 2

- episode_return: `-81.079085`
- steps: `516`

