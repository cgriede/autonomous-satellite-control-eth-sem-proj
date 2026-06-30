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
- created_utc: `2026-06-30T00:39:02.087955+00:00`

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

- episode_return: `-94.316164`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `53.741642`
- pi_loss_mean: `-9.789949`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-52.078698`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `163.494768`
- pi_loss_mean: `-24.184880`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-29.922604`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `295.595425`
- pi_loss_mean: `-32.784974`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-92.794451`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `341.147341`
- pi_loss_mean: `-36.996585`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-75.594459`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `346.342624`
- pi_loss_mean: `-43.058207`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-64.696700`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `456.027358`
- pi_loss_mean: `-50.294823`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `25.415067`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1234.922051`
- pi_loss_mean: `-62.895456`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-17.645593`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1857.126048`
- pi_loss_mean: `-82.997528`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-21.107550`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2322.695709`
- pi_loss_mean: `-103.860373`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-27.322103`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2469.034504`
- pi_loss_mean: `-115.098348`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-41.338303`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2391.294881`
- pi_loss_mean: `-117.255660`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-41.746184`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2238.146498`
- pi_loss_mean: `-117.890641`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-87.407951`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2011.962356`
- pi_loss_mean: `-122.789039`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-83.401820`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2172.799888`
- pi_loss_mean: `-130.733321`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-82.052740`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1741.297958`
- pi_loss_mean: `-141.893822`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-84.121994`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1501.557748`
- pi_loss_mean: `-153.302841`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-78.325594`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1381.612546`
- pi_loss_mean: `-164.334456`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-73.525268`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1098.230630`
- pi_loss_mean: `-177.782595`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-67.949491`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `906.016998`
- pi_loss_mean: `-187.497268`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-72.578912`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `786.911446`
- pi_loss_mean: `-196.750197`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-72.815949`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `702.622128`
- pi_loss_mean: `-205.234212`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-63.617486`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `673.265689`
- pi_loss_mean: `-209.059853`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-68.842557`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `598.793967`
- pi_loss_mean: `-209.037370`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-50.740693`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `525.547971`
- pi_loss_mean: `-203.994649`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-68.528529`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `514.765549`
- pi_loss_mean: `-195.024510`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-38.796227`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `561.013417`
- pi_loss_mean: `-188.208550`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `7.980430`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `450.080450`
- pi_loss_mean: `-185.321658`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-77.905875`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `366.923405`
- pi_loss_mean: `-180.495203`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-76.899957`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `295.180341`
- pi_loss_mean: `-177.013485`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-27.655899`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `258.541035`
- pi_loss_mean: `-173.920390`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-17.166297`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `228.872934`
- pi_loss_mean: `-172.581227`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-61.723821`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `213.048086`
- pi_loss_mean: `-170.697053`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-23.153767`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `201.027961`
- pi_loss_mean: `-169.610040`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-1.383107`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `177.401730`
- pi_loss_mean: `-167.651805`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-4.322587`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `170.824983`
- pi_loss_mean: `-165.708819`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-11.142851`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `156.148714`
- pi_loss_mean: `-161.905176`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `7.976138`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `132.839818`
- pi_loss_mean: `-159.585844`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-6.330479`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `117.625721`
- pi_loss_mean: `-155.706231`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-11.953360`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `108.698355`
- pi_loss_mean: `-152.806396`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `1.477511`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `98.423262`
- pi_loss_mean: `-149.419619`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-42.340253`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `87.266639`
- pi_loss_mean: `-144.929469`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-37.331551`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `84.795923`
- pi_loss_mean: `-141.598700`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `20.175154`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `79.473832`
- pi_loss_mean: `-137.478497`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-11.404283`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `75.991190`
- pi_loss_mean: `-131.945621`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `24.036840`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `72.916376`
- pi_loss_mean: `-128.185173`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-28.772449`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `70.302145`
- pi_loss_mean: `-123.357201`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-6.266727`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `65.361868`
- pi_loss_mean: `-118.785388`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-3.594002`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `70.224132`
- pi_loss_mean: `-113.645013`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-36.018163`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `62.413041`
- pi_loss_mean: `-108.964903`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `104.714333`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `61.895722`
- pi_loss_mean: `-105.066147`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `32.411447`
- steps: `516`

### Eval episode 2

- episode_return: `32.411447`
- steps: `516`

