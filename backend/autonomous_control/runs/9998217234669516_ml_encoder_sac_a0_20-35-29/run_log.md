# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `encoder sac a0`
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
- created_utc: `2026-06-29T20:35:30.484938+00:00`

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

- episode_return: `-72.204179`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `60.615853`
- pi_loss_mean: `-11.071509`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-75.037455`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `126.611961`
- pi_loss_mean: `-32.475377`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-74.426750`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `434.511553`
- pi_loss_mean: `-51.146541`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-78.051055`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `766.424015`
- pi_loss_mean: `-66.591912`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-78.663192`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1091.737042`
- pi_loss_mean: `-78.816138`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-78.273449`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1265.128876`
- pi_loss_mean: `-86.619173`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-80.863353`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1260.210716`
- pi_loss_mean: `-90.237966`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-82.903052`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1259.870778`
- pi_loss_mean: `-91.513897`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-78.571157`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1131.252554`
- pi_loss_mean: `-91.939428`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-77.231877`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `992.447191`
- pi_loss_mean: `-89.812163`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-72.857971`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `826.068078`
- pi_loss_mean: `-86.519795`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-72.927022`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `709.133674`
- pi_loss_mean: `-81.686051`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-73.011898`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `633.219025`
- pi_loss_mean: `-78.193474`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-73.492558`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `602.297149`
- pi_loss_mean: `-74.505535`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-72.602496`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `528.941196`
- pi_loss_mean: `-69.360899`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-73.791231`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `479.618288`
- pi_loss_mean: `-66.310443`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-72.561546`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `459.354591`
- pi_loss_mean: `-62.647213`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-73.163668`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `383.952490`
- pi_loss_mean: `-56.359192`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-74.404226`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `348.066204`
- pi_loss_mean: `-51.696048`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-29.632134`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `357.021248`
- pi_loss_mean: `-48.765040`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-73.880827`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `382.773678`
- pi_loss_mean: `-51.199684`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-70.657314`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `381.490128`
- pi_loss_mean: `-50.686473`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-71.445158`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `243.759475`
- pi_loss_mean: `-44.892529`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-78.683552`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `342.400570`
- pi_loss_mean: `-48.411383`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-78.208789`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `400.738778`
- pi_loss_mean: `-60.416192`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-48.099394`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `405.577934`
- pi_loss_mean: `-68.906427`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-74.305028`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `376.171099`
- pi_loss_mean: `-72.658303`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-72.054068`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `375.430159`
- pi_loss_mean: `-71.204688`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-70.951168`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `339.538281`
- pi_loss_mean: `-64.278946`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-70.749660`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `309.840858`
- pi_loss_mean: `-57.810544`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-70.128730`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `285.157921`
- pi_loss_mean: `-50.007438`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-70.510131`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `310.563799`
- pi_loss_mean: `-44.251763`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-54.601082`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `279.347116`
- pi_loss_mean: `-42.943801`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-49.528555`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `328.988927`
- pi_loss_mean: `-45.752952`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-7.203060`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `373.630446`
- pi_loss_mean: `-48.038452`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-36.943949`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `349.365224`
- pi_loss_mean: `-49.999284`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-25.468375`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `425.004371`
- pi_loss_mean: `-51.771887`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-46.775088`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `449.940826`
- pi_loss_mean: `-50.937755`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-59.264684`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `483.823785`
- pi_loss_mean: `-51.795156`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-7.255815`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `476.810400`
- pi_loss_mean: `-52.403553`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-27.329036`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `501.973152`
- pi_loss_mean: `-51.304286`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-69.929993`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `517.943106`
- pi_loss_mean: `-51.071720`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `4.070932`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `425.125766`
- pi_loss_mean: `-50.127676`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-34.990652`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `343.350956`
- pi_loss_mean: `-50.414689`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `25.194972`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `295.822599`
- pi_loss_mean: `-49.466548`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-23.663807`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `234.808203`
- pi_loss_mean: `-48.883090`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-16.307729`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `195.267011`
- pi_loss_mean: `-48.644496`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-39.665654`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `150.744570`
- pi_loss_mean: `-47.483513`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `27.120249`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `123.069442`
- pi_loss_mean: `-45.959569`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `-26.584290`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `105.341231`
- pi_loss_mean: `-44.584790`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-12.110828`
- steps: `516`

### Eval episode 2

- episode_return: `27.751698`
- steps: `516`

