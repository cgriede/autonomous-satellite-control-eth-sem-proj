# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo decoupled dual vector`
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
- created_utc: `2026-06-30T22:15:02.889157+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `3.002716`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `0.000000`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `0.000000`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `4.644787`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `4.394641`
- steps: `516`

### Train episode 1

- episode_return: `-690.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.118164`
- pi_loss_mean: `-0.170349`
- kl_mean: `-0.121850`
- eta_mean: `2.197547`

### Train episode 2

- episode_return: `-555.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.122942`
- pi_loss_mean: `-0.226687`
- kl_mean: `-0.071964`
- eta_mean: `1.617137`

### Train episode 3

- episode_return: `-315.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.105294`
- pi_loss_mean: `-0.283954`
- kl_mean: `-0.006120`
- eta_mean: `1.270207`

### Train episode 4

- episode_return: `-150.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.105118`
- pi_loss_mean: `-0.324253`
- kl_mean: `0.031740`
- eta_mean: `0.907348`

### Train episode 5

- episode_return: `-15.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.088317`
- pi_loss_mean: `-0.383543`
- kl_mean: `0.038673`
- eta_mean: `0.622204`

### Train episode 6

- episode_return: `-4.181398`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.099840`
- pi_loss_mean: `-0.437041`
- kl_mean: `0.027707`
- eta_mean: `0.440518`

### Train episode 7

- episode_return: `-0.296800`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.117504`
- pi_loss_mean: `-0.470318`
- kl_mean: `0.016252`
- eta_mean: `0.323675`

### Train episode 8

- episode_return: `4.158508`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.125427`
- pi_loss_mean: `-0.487800`
- kl_mean: `0.009879`
- eta_mean: `0.246440`

### Train episode 9

- episode_return: `15.702515`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.148718`
- pi_loss_mean: `-0.495362`
- kl_mean: `0.008440`
- eta_mean: `0.197487`

### Train episode 10

- episode_return: `16.945570`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.166165`
- pi_loss_mean: `-0.499446`
- kl_mean: `0.009949`
- eta_mean: `0.170000`

### Train episode 11

- episode_return: `-3.137771`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.192103`
- pi_loss_mean: `-0.504058`
- kl_mean: `0.007540`
- eta_mean: `0.144107`

### Train episode 12

- episode_return: `-60.817276`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.202838`
- pi_loss_mean: `-0.507132`
- kl_mean: `0.006243`
- eta_mean: `0.115725`

### Train episode 13

- episode_return: `9.836009`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.235024`
- pi_loss_mean: `-0.509060`
- kl_mean: `0.007539`
- eta_mean: `0.092954`

### Train episode 14

- episode_return: `22.029701`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.232630`
- pi_loss_mean: `-0.510308`
- kl_mean: `0.007271`
- eta_mean: `0.074733`

### Train episode 15

- episode_return: `30.949307`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.260068`
- pi_loss_mean: `-0.511413`
- kl_mean: `0.008577`
- eta_mean: `0.060341`

### Train episode 16

- episode_return: `15.548163`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.346351`
- pi_loss_mean: `-0.512019`
- kl_mean: `0.009378`
- eta_mean: `0.048927`

### Train episode 17

- episode_return: `30.474746`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.428058`
- pi_loss_mean: `-0.513258`
- kl_mean: `0.010614`
- eta_mean: `0.039301`

### Train episode 18

- episode_return: `28.281646`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.417216`
- pi_loss_mean: `-0.513081`
- kl_mean: `0.014189`
- eta_mean: `0.031435`

### Train episode 19

- episode_return: `-83.834736`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.547780`
- pi_loss_mean: `-0.510098`
- kl_mean: `0.029682`
- eta_mean: `0.026442`

### Train episode 20

- episode_return: `38.027778`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.442709`
- pi_loss_mean: `-0.511037`
- kl_mean: `0.014060`
- eta_mean: `0.022622`

### Train episode 21

- episode_return: `43.867600`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.583906`
- pi_loss_mean: `-0.504454`
- kl_mean: `0.045059`
- eta_mean: `0.020187`

### Train episode 22

- episode_return: `16.890205`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.669755`
- pi_loss_mean: `-0.506330`
- kl_mean: `0.025851`
- eta_mean: `0.018295`

### Train episode 23

- episode_return: `-101.489342`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.518801`
- pi_loss_mean: `-0.505751`
- kl_mean: `0.029733`
- eta_mean: `0.016346`

### Train episode 24

- episode_return: `36.519398`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.521806`
- pi_loss_mean: `-0.506417`
- kl_mean: `0.020281`
- eta_mean: `0.014618`

### Train episode 25

- episode_return: `30.931391`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.530542`
- pi_loss_mean: `-0.504857`
- kl_mean: `0.020745`
- eta_mean: `0.013407`

### Train episode 26

- episode_return: `34.386516`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.415109`
- pi_loss_mean: `-0.506380`
- kl_mean: `0.013994`
- eta_mean: `0.013190`

### Train episode 27

- episode_return: `12.016473`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.408654`
- pi_loss_mean: `-0.506455`
- kl_mean: `0.012872`
- eta_mean: `0.012536`

### Train episode 28

- episode_return: `48.726613`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.457065`
- pi_loss_mean: `-0.505349`
- kl_mean: `0.021198`
- eta_mean: `0.013292`

### Train episode 29

- episode_return: `32.695335`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.447451`
- pi_loss_mean: `-0.506658`
- kl_mean: `0.018759`
- eta_mean: `0.012737`

### Train episode 30

- episode_return: `28.787201`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.446335`
- pi_loss_mean: `-0.500653`
- kl_mean: `0.040740`
- eta_mean: `0.013113`

### Train episode 31

- episode_return: `45.893203`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.427674`
- pi_loss_mean: `-0.501349`
- kl_mean: `0.024117`
- eta_mean: `0.016410`

### Train episode 32

- episode_return: `55.016409`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.466302`
- pi_loss_mean: `-0.502932`
- kl_mean: `0.018636`
- eta_mean: `0.018015`

### Train episode 33

- episode_return: `46.846006`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.366292`
- pi_loss_mean: `-0.503745`
- kl_mean: `0.016300`
- eta_mean: `0.019125`

### Train episode 34

- episode_return: `28.787201`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.431667`
- pi_loss_mean: `-0.504049`
- kl_mean: `0.016119`
- eta_mean: `0.019008`

### Train episode 35

- episode_return: `21.306588`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.379561`
- pi_loss_mean: `-0.504490`
- kl_mean: `0.012589`
- eta_mean: `0.019672`

### Train episode 36

- episode_return: `36.989184`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.390776`
- pi_loss_mean: `-0.504600`
- kl_mean: `0.016911`
- eta_mean: `0.020144`

### Train episode 37

- episode_return: `70.104797`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.473478`
- pi_loss_mean: `-0.505379`
- kl_mean: `0.018001`
- eta_mean: `0.018198`

### Train episode 38

- episode_return: `39.277825`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.457038`
- pi_loss_mean: `-0.505791`
- kl_mean: `0.021155`
- eta_mean: `0.015614`

### Train episode 39

- episode_return: `49.664598`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.431940`
- pi_loss_mean: `-0.506550`
- kl_mean: `0.019833`
- eta_mean: `0.013798`

### Train episode 40

- episode_return: `72.315811`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.448782`
- pi_loss_mean: `-0.507742`
- kl_mean: `0.016165`
- eta_mean: `0.011824`

### Train episode 41

- episode_return: `30.007170`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.411193`
- pi_loss_mean: `-0.508057`
- kl_mean: `0.019678`
- eta_mean: `0.009678`

### Train episode 42

- episode_return: `30.564962`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.428765`
- pi_loss_mean: `-0.508324`
- kl_mean: `0.017011`
- eta_mean: `0.008111`

### Train episode 43

- episode_return: `82.327710`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.455078`
- pi_loss_mean: `-0.507499`
- kl_mean: `0.023751`
- eta_mean: `0.007345`

### Train episode 44

- episode_return: `70.550097`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.398966`
- pi_loss_mean: `-0.503784`
- kl_mean: `0.035422`
- eta_mean: `0.007107`

### Train episode 45

- episode_return: `49.830582`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.446139`
- pi_loss_mean: `-0.504860`
- kl_mean: `0.029129`
- eta_mean: `0.006854`

### Train episode 46

- episode_return: `30.007170`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.588434`
- pi_loss_mean: `-0.506887`
- kl_mean: `0.018358`
- eta_mean: `0.006205`

### Train episode 47

- episode_return: `72.595854`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.949829`
- pi_loss_mean: `-0.505724`
- kl_mean: `0.019465`
- eta_mean: `0.005824`

### Train episode 48

- episode_return: `49.830582`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.024833`
- pi_loss_mean: `-0.503818`
- kl_mean: `0.016736`
- eta_mean: `0.007495`

### Train episode 49

- episode_return: `51.483655`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.155550`
- pi_loss_mean: `-0.503798`
- kl_mean: `0.014186`
- eta_mean: `0.010189`

### Train episode 50

- episode_return: `62.362945`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.230150`
- pi_loss_mean: `-0.503722`
- kl_mean: `0.020071`
- eta_mean: `0.014187`

### Eval episode 1

- episode_return: `45.540228`
- steps: `516`

### Eval episode 2

- episode_return: `45.540228`
- steps: `516`

