# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `sac shutter reward split waste_off`
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
- created_utc: `2026-06-30T15:43:21.097538+00:00`

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

- episode_return: `-120.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.394040`
- pi_loss_mean: `0.563102`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `54.706880`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.708809`
- pi_loss_mean: `0.587542`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `33.014928`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.124416`
- pi_loss_mean: `0.571167`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `50.726904`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.932828`
- pi_loss_mean: `0.417214`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `1.184708`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.427179`
- pi_loss_mean: `0.250161`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-8.337303`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.047960`
- pi_loss_mean: `0.085945`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `12.513174`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7.725877`
- pi_loss_mean: `-0.112788`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-24.986683`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8.408414`
- pi_loss_mean: `-0.189650`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `80.805866`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `9.919057`
- pi_loss_mean: `-0.245791`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `0.784910`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7.065389`
- pi_loss_mean: `-0.385817`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `11.231257`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7.181287`
- pi_loss_mean: `-0.450491`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `36.756230`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.274286`
- pi_loss_mean: `-0.455802`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `0.765048`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.018006`
- pi_loss_mean: `-0.472285`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-2.263804`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.012824`
- pi_loss_mean: `-0.509990`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `41.869222`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.973271`
- pi_loss_mean: `-0.592241`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `34.382753`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.159143`
- pi_loss_mean: `-0.711098`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `83.744119`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.891001`
- pi_loss_mean: `-0.784082`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-14.301434`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.015056`
- pi_loss_mean: `-0.781400`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-42.630144`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.566142`
- pi_loss_mean: `-0.786859`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-3.389827`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.986021`
- pi_loss_mean: `-0.690952`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `56.098256`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.766411`
- pi_loss_mean: `-0.740987`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `70.088925`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.692508`
- pi_loss_mean: `-0.704861`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `127.755416`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.472326`
- pi_loss_mean: `-0.676202`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `81.931635`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.267024`
- pi_loss_mean: `-0.689772`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `12.173524`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.449401`
- pi_loss_mean: `-0.711317`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `46.201775`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.573928`
- pi_loss_mean: `-0.691629`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `68.163564`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.134032`
- pi_loss_mean: `-0.673776`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `26.752257`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.161485`
- pi_loss_mean: `-0.662410`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `58.752246`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.796797`
- pi_loss_mean: `-0.616646`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `36.596862`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.163511`
- pi_loss_mean: `-0.566918`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `31.604510`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.959464`
- pi_loss_mean: `-0.547280`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-16.121787`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.492121`
- pi_loss_mean: `-0.504770`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `62.641086`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.086163`
- pi_loss_mean: `-0.492644`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `20.533786`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.625804`
- pi_loss_mean: `-0.499709`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `13.448977`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.084905`
- pi_loss_mean: `-0.538949`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `63.247917`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.787776`
- pi_loss_mean: `-0.555121`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `169.917110`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.234192`
- pi_loss_mean: `-0.549618`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-1.267006`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.956495`
- pi_loss_mean: `-0.562965`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `87.773692`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7.135123`
- pi_loss_mean: `-0.592435`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `77.629974`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.827454`
- pi_loss_mean: `-0.632627`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `133.956642`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.276581`
- pi_loss_mean: `-0.628426`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `26.592878`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.251041`
- pi_loss_mean: `-0.634649`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `53.426827`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.697017`
- pi_loss_mean: `-0.653074`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `18.487075`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.336817`
- pi_loss_mean: `-0.654783`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-0.553495`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.238022`
- pi_loss_mean: `-0.640364`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-30.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7.069358`
- pi_loss_mean: `-0.613430`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-16.030228`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.228942`
- pi_loss_mean: `-0.599814`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-32.400089`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.749404`
- pi_loss_mean: `-0.561166`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-3.544452`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.468172`
- pi_loss_mean: `-0.541176`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `95.010865`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.909288`
- pi_loss_mean: `-0.472921`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `106.360747`
- steps: `516`

### Eval episode 2

- episode_return: `106.360747`
- steps: `516`

