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
- created_utc: `2026-06-29T21:19:44.984556+00:00`

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

- episode_return: `-75.645791`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `54.770801`
- pi_loss_mean: `-10.125130`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-45.391486`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `169.056308`
- pi_loss_mean: `-25.736170`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `8.993455`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `349.016419`
- pi_loss_mean: `-40.388247`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-30.626009`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `498.710907`
- pi_loss_mean: `-52.676225`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-54.594827`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1014.091427`
- pi_loss_mean: `-66.291968`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `8.264339`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1433.504676`
- pi_loss_mean: `-79.275493`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-40.876088`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2150.076847`
- pi_loss_mean: `-93.427664`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-27.967792`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2407.597780`
- pi_loss_mean: `-108.961951`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-36.881935`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2852.239856`
- pi_loss_mean: `-123.990940`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-79.685594`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2656.539786`
- pi_loss_mean: `-128.094123`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-77.425434`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2576.395320`
- pi_loss_mean: `-128.330968`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-75.004099`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2946.806398`
- pi_loss_mean: `-127.578265`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-76.994722`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3315.234413`
- pi_loss_mean: `-129.538103`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-77.353511`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3781.618364`
- pi_loss_mean: `-134.309614`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-73.757205`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4388.084547`
- pi_loss_mean: `-139.177211`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-77.502248`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5921.796141`
- pi_loss_mean: `-148.822318`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-74.610394`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6981.164863`
- pi_loss_mean: `-157.594050`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-76.648748`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8731.704675`
- pi_loss_mean: `-164.645608`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-74.064695`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8451.621872`
- pi_loss_mean: `-175.198427`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-73.835817`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `13001.892050`
- pi_loss_mean: `-172.347219`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-84.323002`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `25114.133918`
- pi_loss_mean: `-192.266788`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-85.399379`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `17196.669158`
- pi_loss_mean: `-202.150678`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-72.619183`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `14596.122137`
- pi_loss_mean: `-208.906901`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-35.822726`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `42588.948281`
- pi_loss_mean: `-205.315676`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-14.269754`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `31120.586621`
- pi_loss_mean: `-208.439172`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-72.136589`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `23961.246629`
- pi_loss_mean: `-204.423401`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-57.656060`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `31295.232104`
- pi_loss_mean: `-197.919693`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-33.985988`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `26896.556501`
- pi_loss_mean: `-192.574298`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-74.204503`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `21270.330997`
- pi_loss_mean: `-172.460070`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-75.319635`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `21332.759080`
- pi_loss_mean: `-158.610906`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-66.722089`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `21902.167744`
- pi_loss_mean: `-139.607441`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-77.568491`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `18569.182499`
- pi_loss_mean: `-123.978395`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-75.289465`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `13949.968919`
- pi_loss_mean: `-111.044172`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-37.558785`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `22415.507893`
- pi_loss_mean: `-95.922764`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-73.125835`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `12980.327083`
- pi_loss_mean: `-78.671108`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-73.763801`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `17139.837432`
- pi_loss_mean: `-68.487734`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-78.106841`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `22205.492142`
- pi_loss_mean: `-48.941873`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-74.988218`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10123.475575`
- pi_loss_mean: `-38.305124`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-76.535324`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10764.688672`
- pi_loss_mean: `-30.102266`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-34.492720`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `20477.946161`
- pi_loss_mean: `-18.636611`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-25.371574`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `14831.138862`
- pi_loss_mean: `-8.426474`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-39.985686`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10225.242898`
- pi_loss_mean: `-5.866480`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-71.822388`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7221.596272`
- pi_loss_mean: `-0.638835`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-66.505856`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5503.954693`
- pi_loss_mean: `2.970593`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-63.935854`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4991.956888`
- pi_loss_mean: `11.558768`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-38.040711`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4381.188781`
- pi_loss_mean: `5.398760`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-37.433425`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3709.163675`
- pi_loss_mean: `4.032684`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-41.504946`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3444.189405`
- pi_loss_mean: `5.736647`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-29.182720`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2717.797641`
- pi_loss_mean: `4.430528`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `-51.646187`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2398.123291`
- pi_loss_mean: `6.427990`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-21.575339`
- steps: `516`

### Eval episode 2

- episode_return: `-21.575339`
- steps: `516`

