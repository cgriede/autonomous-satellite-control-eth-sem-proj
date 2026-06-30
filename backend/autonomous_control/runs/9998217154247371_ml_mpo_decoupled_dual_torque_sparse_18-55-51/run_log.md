# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo decoupled dual torque`
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
- created_utc: `2026-06-30T18:55:52.629084+00:00`

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

- episode_return: `-808.158313`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `34.973473`
- pi_loss_mean: `-0.172946`
- kl_mean: `-0.116714`
- eta_mean: `3.213595`

### Train episode 2

- episode_return: `-805.028940`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `59.071499`
- pi_loss_mean: `-0.241855`
- kl_mean: `-0.060410`
- eta_mean: `5.421575`

### Train episode 3

- episode_return: `-496.229514`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `135.580907`
- pi_loss_mean: `-0.304938`
- kl_mean: `0.003846`
- eta_mean: `7.148745`

### Train episode 4

- episode_return: `-292.467008`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `232.398763`
- pi_loss_mean: `-0.342495`
- kl_mean: `0.034585`
- eta_mean: `6.185439`

### Train episode 5

- episode_return: `-132.459422`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `382.053315`
- pi_loss_mean: `-0.381657`
- kl_mean: `0.029318`
- eta_mean: `4.696818`

### Train episode 6

- episode_return: `-107.888016`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `534.372002`
- pi_loss_mean: `-0.416398`
- kl_mean: `0.026822`
- eta_mean: `3.843990`

### Train episode 7

- episode_return: `-55.503151`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `649.775116`
- pi_loss_mean: `-0.445812`
- kl_mean: `0.021220`
- eta_mean: `3.281874`

### Train episode 8

- episode_return: `-74.393061`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `792.255169`
- pi_loss_mean: `-0.464772`
- kl_mean: `0.014905`
- eta_mean: `3.008969`

### Train episode 9

- episode_return: `-80.615603`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `989.811100`
- pi_loss_mean: `-0.475571`
- kl_mean: `0.012838`
- eta_mean: `3.117892`

### Train episode 10

- episode_return: `-27.697364`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1231.767065`
- pi_loss_mean: `-0.483101`
- kl_mean: `0.015040`
- eta_mean: `3.438187`

### Train episode 11

- episode_return: `-9.951334`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1970.626533`
- pi_loss_mean: `-0.489863`
- kl_mean: `0.013770`
- eta_mean: `3.103611`

### Train episode 12

- episode_return: `-20.949142`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4202.265760`
- pi_loss_mean: `-0.494838`
- kl_mean: `0.012182`
- eta_mean: `2.406161`

### Train episode 13

- episode_return: `-66.064490`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4713.680020`
- pi_loss_mean: `-0.496352`
- kl_mean: `0.010128`
- eta_mean: `1.984731`

### Train episode 14

- episode_return: `-61.033737`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5796.979279`
- pi_loss_mean: `-0.495337`
- kl_mean: `0.013703`
- eta_mean: `2.149713`

### Train episode 15

- episode_return: `-29.991015`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5977.180531`
- pi_loss_mean: `-0.495793`
- kl_mean: `0.013219`
- eta_mean: `2.438520`

### Train episode 16

- episode_return: `-50.103154`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6391.437663`
- pi_loss_mean: `-0.494819`
- kl_mean: `0.017239`
- eta_mean: `3.064869`

### Train episode 17

- episode_return: `-50.553741`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8915.603821`
- pi_loss_mean: `-0.492595`
- kl_mean: `0.024793`
- eta_mean: `3.920979`

### Train episode 18

- episode_return: `-54.793244`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8710.962477`
- pi_loss_mean: `-0.491191`
- kl_mean: `0.024486`
- eta_mean: `5.973056`

### Train episode 19

- episode_return: `-54.829132`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8806.155234`
- pi_loss_mean: `-0.491239`
- kl_mean: `0.019884`
- eta_mean: `7.101871`

### Train episode 20

- episode_return: `-55.057570`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7465.817319`
- pi_loss_mean: `-0.491526`
- kl_mean: `0.018694`
- eta_mean: `6.968192`

### Train episode 21

- episode_return: `-49.705431`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7742.177114`
- pi_loss_mean: `-0.491386`
- kl_mean: `0.021414`
- eta_mean: `6.940327`

### Train episode 22

- episode_return: `-50.560023`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7604.036177`
- pi_loss_mean: `-0.491789`
- kl_mean: `0.020509`
- eta_mean: `6.636746`

### Train episode 23

- episode_return: `-50.495898`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10133.975410`
- pi_loss_mean: `-0.491120`
- kl_mean: `0.021462`
- eta_mean: `6.677049`

### Train episode 24

- episode_return: `-50.729028`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10228.738602`
- pi_loss_mean: `-0.490946`
- kl_mean: `0.021847`
- eta_mean: `6.594753`

### Train episode 25

- episode_return: `-50.691988`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `10905.502096`
- pi_loss_mean: `-0.491886`
- kl_mean: `0.020390`
- eta_mean: `6.033567`

### Train episode 26

- episode_return: `-50.994994`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `12704.027329`
- pi_loss_mean: `-0.494238`
- kl_mean: `0.017862`
- eta_mean: `4.868941`

### Train episode 27

- episode_return: `-51.185906`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `16880.682753`
- pi_loss_mean: `-0.495771`
- kl_mean: `0.018650`
- eta_mean: `3.940832`

### Train episode 28

- episode_return: `-50.698103`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `16627.386353`
- pi_loss_mean: `-0.496709`
- kl_mean: `0.018205`
- eta_mean: `3.465594`

### Train episode 29

- episode_return: `-50.750074`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `28001.828397`
- pi_loss_mean: `-0.496338`
- kl_mean: `0.021280`
- eta_mean: `3.170065`

### Train episode 30

- episode_return: `-50.981623`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `18308.064434`
- pi_loss_mean: `-0.497253`
- kl_mean: `0.019065`
- eta_mean: `2.746787`

### Train episode 31

- episode_return: `-50.928972`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `29672.617086`
- pi_loss_mean: `-0.496391`
- kl_mean: `0.020575`
- eta_mean: `2.556868`

### Train episode 32

- episode_return: `-50.984894`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `33034.288913`
- pi_loss_mean: `-0.495924`
- kl_mean: `0.020753`
- eta_mean: `2.660766`

### Train episode 33

- episode_return: `-50.762204`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `39786.339522`
- pi_loss_mean: `-0.496932`
- kl_mean: `0.019849`
- eta_mean: `2.403980`

### Train episode 34

- episode_return: `-51.038924`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `30463.373056`
- pi_loss_mean: `-0.497097`
- kl_mean: `0.019311`
- eta_mean: `2.234969`

### Train episode 35

- episode_return: `-51.062019`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `39967.692189`
- pi_loss_mean: `-0.495488`
- kl_mean: `0.021647`
- eta_mean: `2.287370`

### Train episode 36

- episode_return: `-50.842847`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `66798.558509`
- pi_loss_mean: `-0.494705`
- kl_mean: `0.021470`
- eta_mean: `2.525804`

### Train episode 37

- episode_return: `-50.710992`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `53693.630387`
- pi_loss_mean: `-0.495285`
- kl_mean: `0.019164`
- eta_mean: `2.637689`

### Train episode 38

- episode_return: `-50.990771`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `55294.429300`
- pi_loss_mean: `-0.494460`
- kl_mean: `0.021970`
- eta_mean: `2.642622`

### Train episode 39

- episode_return: `-50.584218`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `63048.318581`
- pi_loss_mean: `-0.491359`
- kl_mean: `0.022432`
- eta_mean: `3.438549`

### Train episode 40

- episode_return: `-50.585743`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `106171.874792`
- pi_loss_mean: `-0.492834`
- kl_mean: `0.019816`
- eta_mean: `3.879934`

### Train episode 41

- episode_return: `-50.533700`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `103964.732774`
- pi_loss_mean: `-0.492953`
- kl_mean: `0.019917`
- eta_mean: `3.649472`

### Train episode 42

- episode_return: `-50.868798`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `63961.697623`
- pi_loss_mean: `-0.493756`
- kl_mean: `0.020236`
- eta_mean: `3.492152`

### Train episode 43

- episode_return: `-50.420512`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `162962.984477`
- pi_loss_mean: `-0.494908`
- kl_mean: `0.018048`
- eta_mean: `3.320244`

### Train episode 44

- episode_return: `-51.003329`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `176579.562070`
- pi_loss_mean: `-0.493933`
- kl_mean: `0.021471`
- eta_mean: `3.319947`

### Train episode 45

- episode_return: `-50.374584`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `232845.550534`
- pi_loss_mean: `-0.493366`
- kl_mean: `0.023106`
- eta_mean: `3.958216`

### Train episode 46

- episode_return: `-50.599712`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `246931.642180`
- pi_loss_mean: `-0.497601`
- kl_mean: `0.015593`
- eta_mean: `3.515858`

### Train episode 47

- episode_return: `-50.478951`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `270699.913870`
- pi_loss_mean: `-0.498775`
- kl_mean: `0.015477`
- eta_mean: `2.780847`

