# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `agent reference ref1`
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
- created_utc: `2026-06-30T11:05:57.186204+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `-41.950589`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `-59.950004`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `-59.939624`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `-40.309062`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `-40.566543`
- steps: `516`

### Train episode 1

- episode_return: `-97.895569`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.363434`
- pi_loss_mean: `0.563287`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-6.765523`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.412998`
- pi_loss_mean: `0.564508`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-17.737124`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.330373`
- pi_loss_mean: `0.164261`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-87.472767`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.882160`
- pi_loss_mean: `-0.256862`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-42.886808`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.984779`
- pi_loss_mean: `-0.424000`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-42.907525`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.693334`
- pi_loss_mean: `-0.543714`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-49.433584`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.755597`
- pi_loss_mean: `-0.671793`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-4.054307`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.711777`
- pi_loss_mean: `-0.808567`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-47.470538`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.483256`
- pi_loss_mean: `-0.989017`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-39.791820`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.480553`
- pi_loss_mean: `-1.182500`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-72.176037`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.335003`
- pi_loss_mean: `-1.297070`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `95.768188`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.219408`
- pi_loss_mean: `-1.373566`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-30.032996`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.543773`
- pi_loss_mean: `-1.508332`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-13.258344`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.730795`
- pi_loss_mean: `-1.586212`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-63.036587`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.781770`
- pi_loss_mean: `-1.639319`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-65.443339`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.732528`
- pi_loss_mean: `-1.701717`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-62.212256`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.006875`
- pi_loss_mean: `-1.788921`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-77.472077`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.878981`
- pi_loss_mean: `-1.807596`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-89.822768`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.863178`
- pi_loss_mean: `-1.896587`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-88.879803`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.400846`
- pi_loss_mean: `-1.820721`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-51.636435`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.418924`
- pi_loss_mean: `-1.871297`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-97.448146`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.178065`
- pi_loss_mean: `-1.882198`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-57.224809`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.517228`
- pi_loss_mean: `-1.723349`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-80.462854`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.199359`
- pi_loss_mean: `-1.741648`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `1.768276`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.992026`
- pi_loss_mean: `-1.650984`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-57.313814`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.900597`
- pi_loss_mean: `-1.576164`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-62.458608`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.113924`
- pi_loss_mean: `-1.445830`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-77.217482`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.045317`
- pi_loss_mean: `-1.460509`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-42.464178`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.639121`
- pi_loss_mean: `-1.567555`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-52.771788`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.277237`
- pi_loss_mean: `-1.783486`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-26.507455`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.622673`
- pi_loss_mean: `-2.192371`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-52.638278`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5.739526`
- pi_loss_mean: `-2.109547`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-74.119237`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.317045`
- pi_loss_mean: `-2.050450`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-8.723949`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.583458`
- pi_loss_mean: `-2.000739`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-86.913812`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.711272`
- pi_loss_mean: `-1.982743`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-62.487297`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4.132397`
- pi_loss_mean: `-1.942735`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-96.562711`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.642585`
- pi_loss_mean: `-1.969777`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-71.063335`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.714270`
- pi_loss_mean: `-1.976955`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-70.176767`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.261962`
- pi_loss_mean: `-1.895338`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-12.242788`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.001855`
- pi_loss_mean: `-1.875944`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-34.392771`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.886874`
- pi_loss_mean: `-1.819724`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-71.108244`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.279858`
- pi_loss_mean: `-1.755236`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-42.172271`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.380732`
- pi_loss_mean: `-1.629844`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `18.667414`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.539244`
- pi_loss_mean: `-1.494156`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-53.975223`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.267815`
- pi_loss_mean: `-1.432927`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-65.649438`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.201799`
- pi_loss_mean: `-1.384855`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-66.006498`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.308862`
- pi_loss_mean: `-1.339758`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `5.414243`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.090431`
- pi_loss_mean: `-1.294697`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-41.915016`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.199728`
- pi_loss_mean: `-1.251296`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `-54.159358`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.841502`
- pi_loss_mean: `-1.260065`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-24.080974`
- steps: `516`

### Eval episode 2

- episode_return: `-24.080974`
- steps: `516`

