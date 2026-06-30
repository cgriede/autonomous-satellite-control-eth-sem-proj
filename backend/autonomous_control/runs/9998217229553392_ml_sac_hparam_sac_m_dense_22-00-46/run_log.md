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
- created_utc: `2026-06-29T22:00:46.608919+00:00`

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

- episode_return: `-74.169372`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `54.727033`
- pi_loss_mean: `-10.748029`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-25.549401`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `124.906234`
- pi_loss_mean: `-25.024510`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-36.966534`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `189.873894`
- pi_loss_mean: `-34.805703`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-16.551492`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `260.499169`
- pi_loss_mean: `-39.118541`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-28.807866`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `943.859762`
- pi_loss_mean: `-48.033566`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-49.556977`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `765.471444`
- pi_loss_mean: `-60.293795`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-30.266208`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `645.320645`
- pi_loss_mean: `-67.628594`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-27.650165`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `527.322931`
- pi_loss_mean: `-74.583783`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-32.504660`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `440.924206`
- pi_loss_mean: `-79.640660`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-62.807000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `655.670590`
- pi_loss_mean: `-81.008173`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-54.204888`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `440.440028`
- pi_loss_mean: `-81.025640`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-68.894466`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `344.306892`
- pi_loss_mean: `-78.942913`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-71.862914`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `273.402293`
- pi_loss_mean: `-73.806886`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-70.381410`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `231.225307`
- pi_loss_mean: `-70.731578`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-69.758332`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `208.164632`
- pi_loss_mean: `-67.987576`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-70.204152`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `169.242556`
- pi_loss_mean: `-65.390754`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-69.105411`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `160.747292`
- pi_loss_mean: `-64.549277`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `24.535228`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `153.434826`
- pi_loss_mean: `-63.236869`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-46.340542`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `142.195674`
- pi_loss_mean: `-62.564772`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-71.348264`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `133.445483`
- pi_loss_mean: `-60.090177`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-60.295278`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `136.987325`
- pi_loss_mean: `-60.405817`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-69.264828`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `133.096234`
- pi_loss_mean: `-58.856564`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-73.227494`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `141.908626`
- pi_loss_mean: `-56.803963`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-51.981412`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `119.327231`
- pi_loss_mean: `-55.184291`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `22.294385`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `130.209628`
- pi_loss_mean: `-53.354795`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-28.174412`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `145.202761`
- pi_loss_mean: `-53.098677`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `1.326133`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `140.708780`
- pi_loss_mean: `-52.962025`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `54.332569`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `136.414795`
- pi_loss_mean: `-52.922340`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-25.395340`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `111.726802`
- pi_loss_mean: `-51.195774`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `181.971877`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `109.852987`
- pi_loss_mean: `-50.635234`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-14.829704`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `103.844122`
- pi_loss_mean: `-49.869335`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `74.847647`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `90.808971`
- pi_loss_mean: `-47.993221`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `5.417830`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `94.197284`
- pi_loss_mean: `-46.348124`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `78.951233`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `104.190604`
- pi_loss_mean: `-45.431689`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-27.736506`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `100.005447`
- pi_loss_mean: `-44.929868`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-13.402516`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `109.371285`
- pi_loss_mean: `-44.005935`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-15.382933`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `94.541405`
- pi_loss_mean: `-42.501349`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `4.239294`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `83.962362`
- pi_loss_mean: `-41.246942`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-37.144663`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `86.773168`
- pi_loss_mean: `-40.739975`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `36.842831`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `75.945533`
- pi_loss_mean: `-39.985973`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `57.715919`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `78.717204`
- pi_loss_mean: `-38.597459`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `61.770046`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `72.526203`
- pi_loss_mean: `-37.707641`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-16.249693`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `73.992797`
- pi_loss_mean: `-36.338240`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `64.075605`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `69.117891`
- pi_loss_mean: `-35.191861`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `11.619111`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `61.842030`
- pi_loss_mean: `-34.080650`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `35.917629`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `64.448549`
- pi_loss_mean: `-33.361573`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `77.853753`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `56.695771`
- pi_loss_mean: `-32.683884`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `13.924902`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `55.733016`
- pi_loss_mean: `-31.531297`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `13.566563`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `54.805039`
- pi_loss_mean: `-30.318518`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `52.880393`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `52.142745`
- pi_loss_mean: `-29.128551`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-41.110713`
- steps: `516`

### Eval episode 2

- episode_return: `-41.110713`
- steps: `516`

