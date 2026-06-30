# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `sac vector budget penalty`
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
- created_utc: `2026-06-30T13:56:19.288375+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `-31.997284`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `-50.000000`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `-50.000000`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `-30.355213`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `-30.605359`
- steps: `516`

### Train episode 1

- episode_return: `-105.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.380321`
- pi_loss_mean: `0.549634`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-72.803586`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.281884`
- pi_loss_mean: `0.531401`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-38.126240`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.290783`
- pi_loss_mean: `0.460287`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-40.574350`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.533682`
- pi_loss_mean: `0.328183`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-30.489149`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.793063`
- pi_loss_mean: `0.113376`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-30.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.893393`
- pi_loss_mean: `0.042198`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-5.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.506366`
- pi_loss_mean: `0.063155`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-26.256470`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.414022`
- pi_loss_mean: `0.053044`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `35.261586`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.915868`
- pi_loss_mean: `0.013096`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-10.503381`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.066964`
- pi_loss_mean: `-0.019028`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `11.175191`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.960834`
- pi_loss_mean: `-0.041680`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `56.218713`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.548345`
- pi_loss_mean: `-0.105627`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-14.007560`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.680000`
- pi_loss_mean: `-0.175968`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-35.943055`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.032714`
- pi_loss_mean: `-0.305637`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-40.277363`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.463638`
- pi_loss_mean: `-0.396161`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-13.567529`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.527841`
- pi_loss_mean: `-0.433964`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-24.930161`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.769338`
- pi_loss_mean: `-0.485563`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-1.861181`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.445297`
- pi_loss_mean: `-0.568943`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-109.779546`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.561783`
- pi_loss_mean: `-0.649772`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `8.428627`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.817988`
- pi_loss_mean: `-0.684443`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-34.931274`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.044717`
- pi_loss_mean: `-0.774148`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `12.392117`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.241255`
- pi_loss_mean: `-0.821494`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-13.139859`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.282661`
- pi_loss_mean: `-0.901050`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `28.114640`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.835080`
- pi_loss_mean: `-0.962256`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-3.416603`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7.224772`
- pi_loss_mean: `-1.005531`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `79.453159`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.634712`
- pi_loss_mean: `-1.071040`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-51.188673`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.468528`
- pi_loss_mean: `-1.105892`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `32.813193`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.648609`
- pi_loss_mean: `-1.017838`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-16.036487`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.910035`
- pi_loss_mean: `-1.007074`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-30.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.900540`
- pi_loss_mean: `-1.004378`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-7.566114`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.853450`
- pi_loss_mean: `-1.033212`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `16.130494`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.212801`
- pi_loss_mean: `-1.020780`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-16.863256`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.687970`
- pi_loss_mean: `-1.010215`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-25.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.267967`
- pi_loss_mean: `-1.002419`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `54.688494`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.457155`
- pi_loss_mean: `-0.981331`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `8.982574`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.965116`
- pi_loss_mean: `-0.976277`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `37.880201`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.796022`
- pi_loss_mean: `-0.975403`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-9.514390`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.142673`
- pi_loss_mean: `-0.976844`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `14.218033`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.728814`
- pi_loss_mean: `-0.945772`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `43.145403`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.807351`
- pi_loss_mean: `-1.029566`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-34.871860`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.570161`
- pi_loss_mean: `-1.014160`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `30.185186`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7.692780`
- pi_loss_mean: `-1.140111`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `124.571917`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.989896`
- pi_loss_mean: `-1.281736`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-23.891598`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.811620`
- pi_loss_mean: `-1.378180`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `14.709298`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8.144219`
- pi_loss_mean: `-1.461097`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `7.559108`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.801470`
- pi_loss_mean: `-1.520187`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-19.279724`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.589170`
- pi_loss_mean: `-1.445208`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `5.429343`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.283972`
- pi_loss_mean: `-1.437245`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `8.450011`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.624007`
- pi_loss_mean: `-1.323554`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `29.915031`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.600572`
- pi_loss_mean: `-1.282797`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `10.581258`
- steps: `516`

### Eval episode 2

- episode_return: `10.581258`
- steps: `516`

