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
- created_utc: `2026-06-29T23:38:00.956871+00:00`

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

- episode_return: `-76.122459`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `55.166231`
- pi_loss_mean: `-10.038422`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-35.762499`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `170.838925`
- pi_loss_mean: `-25.985591`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `12.001741`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `381.100417`
- pi_loss_mean: `-41.739119`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-33.700543`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `517.238496`
- pi_loss_mean: `-56.654252`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-22.159680`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `713.233376`
- pi_loss_mean: `-72.741575`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `0.712588`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1201.475371`
- pi_loss_mean: `-91.083954`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `58.946694`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1796.993680`
- pi_loss_mean: `-114.297288`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-43.468601`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5568.008222`
- pi_loss_mean: `-148.443727`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-44.572863`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6282.048126`
- pi_loss_mean: `-201.337287`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-45.128190`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6832.920857`
- pi_loss_mean: `-230.911038`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-44.460817`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5800.582914`
- pi_loss_mean: `-245.679697`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-44.632196`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5595.680698`
- pi_loss_mean: `-256.036755`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-39.062666`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5528.412886`
- pi_loss_mean: `-266.206041`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-41.905767`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5125.064527`
- pi_loss_mean: `-265.928717`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-39.935233`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4768.489353`
- pi_loss_mean: `-263.996311`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-43.039223`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4528.192366`
- pi_loss_mean: `-260.993808`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-39.047073`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5615.313068`
- pi_loss_mean: `-257.227031`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-42.824807`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5404.080110`
- pi_loss_mean: `-251.640946`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-40.376304`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8310.770390`
- pi_loss_mean: `-243.256910`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-77.010356`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5949.894698`
- pi_loss_mean: `-225.066665`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-24.123791`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4361.820727`
- pi_loss_mean: `-213.418565`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-78.132639`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3890.685542`
- pi_loss_mean: `-200.681570`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-77.832827`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3269.403094`
- pi_loss_mean: `-185.964132`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-79.824484`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3104.085711`
- pi_loss_mean: `-174.211790`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-83.322821`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3235.558603`
- pi_loss_mean: `-160.036092`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-81.593388`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2704.378062`
- pi_loss_mean: `-146.778367`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-81.919577`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2815.784316`
- pi_loss_mean: `-134.402929`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-77.868848`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2702.163259`
- pi_loss_mean: `-121.780324`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-82.256320`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2634.510341`
- pi_loss_mean: `-111.666066`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-78.927265`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2366.235532`
- pi_loss_mean: `-103.592652`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-77.517311`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2505.825560`
- pi_loss_mean: `-95.835068`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-79.309009`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1725.362488`
- pi_loss_mean: `-87.901950`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-75.312333`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1854.686379`
- pi_loss_mean: `-81.014994`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-4.698023`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1621.834739`
- pi_loss_mean: `-75.814614`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `36.215489`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1538.623267`
- pi_loss_mean: `-69.979648`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-27.579728`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1093.743921`
- pi_loss_mean: `-67.092825`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-43.755051`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `667.253432`
- pi_loss_mean: `-64.133802`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-14.437610`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `924.270512`
- pi_loss_mean: `-58.978113`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-57.503032`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `768.501577`
- pi_loss_mean: `-55.469878`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `-67.103314`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `573.366675`
- pi_loss_mean: `-53.259911`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-33.217671`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `431.987116`
- pi_loss_mean: `-49.930416`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-34.664672`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `447.702175`
- pi_loss_mean: `-48.020651`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-30.146617`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `252.162959`
- pi_loss_mean: `-47.206184`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-30.123362`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `241.151898`
- pi_loss_mean: `-47.365975`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-1.423997`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `231.086954`
- pi_loss_mean: `-48.250301`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `38.834519`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `216.355855`
- pi_loss_mean: `-49.332209`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `2.119058`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `231.166940`
- pi_loss_mean: `-50.230508`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-40.862360`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `202.895927`
- pi_loss_mean: `-50.344767`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-30.427483`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `203.823494`
- pi_loss_mean: `-49.095969`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `90.160629`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `191.344305`
- pi_loss_mean: `-49.213910`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `5.411386`
- steps: `516`

### Eval episode 2

- episode_return: `5.411386`
- steps: `516`

