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
- created_utc: `2026-06-30T00:15:59.576961+00:00`

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

- episode_return: `-75.771325`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `55.085672`
- pi_loss_mean: `-10.170949`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-26.411255`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `169.816797`
- pi_loss_mean: `-26.101352`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-17.056602`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `367.347877`
- pi_loss_mean: `-39.218352`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `13.231584`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `485.315521`
- pi_loss_mean: `-48.217651`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `11.452697`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `520.733815`
- pi_loss_mean: `-57.971227`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-48.215644`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `763.915839`
- pi_loss_mean: `-68.780056`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-31.424694`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2871.191383`
- pi_loss_mean: `-92.301618`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-44.194222`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3383.597502`
- pi_loss_mean: `-126.378933`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-40.996444`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3008.791581`
- pi_loss_mean: `-150.077230`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-28.227491`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3060.864478`
- pi_loss_mean: `-168.592621`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `49.359335`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4197.003262`
- pi_loss_mean: `-176.448461`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-29.593866`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5933.433012`
- pi_loss_mean: `-177.055247`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-22.329170`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8925.658241`
- pi_loss_mean: `-185.544321`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-22.643940`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6984.711927`
- pi_loss_mean: `-190.488274`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-23.538704`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6746.462190`
- pi_loss_mean: `-191.977989`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-22.867362`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6254.895989`
- pi_loss_mean: `-193.047825`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-30.897512`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8666.851515`
- pi_loss_mean: `-190.762474`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-29.566113`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10039.090465`
- pi_loss_mean: `-187.175234`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-24.265365`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `22430.075135`
- pi_loss_mean: `-179.500399`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-30.439627`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `16687.692239`
- pi_loss_mean: `-167.652237`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-17.865578`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `14108.330303`
- pi_loss_mean: `-164.849494`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-29.674569`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8960.899409`
- pi_loss_mean: `-154.044952`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-17.031925`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `9202.537382`
- pi_loss_mean: `-143.440665`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-21.100091`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7067.114526`
- pi_loss_mean: `-134.495540`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-64.915033`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7105.731223`
- pi_loss_mean: `-125.766319`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-80.674413`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6965.614289`
- pi_loss_mean: `-116.800910`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-72.864963`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4861.398473`
- pi_loss_mean: `-104.243321`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-67.446500`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5290.131022`
- pi_loss_mean: `-92.073600`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-67.973356`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5103.119165`
- pi_loss_mean: `-79.481484`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-71.938929`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3692.339153`
- pi_loss_mean: `-71.819218`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-72.301597`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4248.297629`
- pi_loss_mean: `-61.557189`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-74.310483`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3987.470884`
- pi_loss_mean: `-51.387886`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-76.753436`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3998.706709`
- pi_loss_mean: `-45.209700`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-77.349023`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3896.780153`
- pi_loss_mean: `-36.938017`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-78.796688`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3207.631959`
- pi_loss_mean: `-30.633280`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-77.687352`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3056.371921`
- pi_loss_mean: `-25.582065`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-79.709989`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3051.347664`
- pi_loss_mean: `-20.027894`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-79.775750`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3862.599516`
- pi_loss_mean: `-16.878979`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-80.809818`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2709.859470`
- pi_loss_mean: `-12.462497`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-77.578325`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3201.360640`
- pi_loss_mean: `-10.594833`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-75.790791`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2636.512618`
- pi_loss_mean: `-6.094597`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-59.280868`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2793.877341`
- pi_loss_mean: `-3.881892`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-79.509644`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3533.041829`
- pi_loss_mean: `1.403423`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-46.502927`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3560.946913`
- pi_loss_mean: `4.456755`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-74.078992`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3357.000449`
- pi_loss_mean: `3.262090`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-24.308211`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3915.840439`
- pi_loss_mean: `5.610628`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-75.872446`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2316.034599`
- pi_loss_mean: `6.223103`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-73.739399`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3607.842859`
- pi_loss_mean: `10.563780`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-73.461941`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2754.063174`
- pi_loss_mean: `12.078241`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `-26.601621`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5381.647252`
- pi_loss_mean: `11.051740`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-33.642492`
- steps: `516`

### Eval episode 2

- episode_return: `-33.642492`
- steps: `516`

