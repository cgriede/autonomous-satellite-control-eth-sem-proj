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
- created_utc: `2026-06-29T22:17:28.396823+00:00`

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

- episode_return: `-73.227478`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `51.801239`
- pi_loss_mean: `-11.905145`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-16.885446`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `85.005408`
- pi_loss_mean: `-21.206568`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-58.818039`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `150.330193`
- pi_loss_mean: `-28.780351`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-72.242879`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `249.010173`
- pi_loss_mean: `-41.466377`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-38.912264`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `707.485901`
- pi_loss_mean: `-59.745254`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-71.102341`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `752.196242`
- pi_loss_mean: `-76.292556`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-53.384867`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `669.009510`
- pi_loss_mean: `-93.548932`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-80.985293`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2385.874556`
- pi_loss_mean: `-109.950356`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-56.474023`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3376.941005`
- pi_loss_mean: `-127.285624`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-33.343810`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1932.809772`
- pi_loss_mean: `-129.986343`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-16.612100`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1320.329488`
- pi_loss_mean: `-134.497410`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-75.732030`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1317.886387`
- pi_loss_mean: `-138.623540`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-75.097741`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1472.556269`
- pi_loss_mean: `-144.314374`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-58.734605`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1486.464353`
- pi_loss_mean: `-155.721025`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-67.094625`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1147.251011`
- pi_loss_mean: `-164.571689`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-73.130074`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1245.461352`
- pi_loss_mean: `-166.523913`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-20.749852`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2499.848985`
- pi_loss_mean: `-175.191093`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-37.449599`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1605.832359`
- pi_loss_mean: `-184.401375`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-29.609810`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1551.654801`
- pi_loss_mean: `-185.435124`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-34.524014`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1677.628379`
- pi_loss_mean: `-181.619682`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-55.028956`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1516.834265`
- pi_loss_mean: `-184.889651`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-62.996589`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1736.120838`
- pi_loss_mean: `-177.523897`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `7.061237`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2665.153296`
- pi_loss_mean: `-173.788526`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-26.804484`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2481.430187`
- pi_loss_mean: `-178.872710`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-70.126370`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1558.906212`
- pi_loss_mean: `-182.236425`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-4.774256`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2574.465102`
- pi_loss_mean: `-183.463236`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-38.558178`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2634.463729`
- pi_loss_mean: `-186.293677`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `41.210560`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2782.379459`
- pi_loss_mean: `-183.133402`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `10.923303`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2142.397392`
- pi_loss_mean: `-184.813580`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-31.806643`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2714.340831`
- pi_loss_mean: `-183.824297`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-69.371310`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2369.278919`
- pi_loss_mean: `-178.047264`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `57.836336`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2196.415647`
- pi_loss_mean: `-174.263767`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `1.234476`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4090.551317`
- pi_loss_mean: `-175.921708`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-40.787998`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2200.071316`
- pi_loss_mean: `-178.439528`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `24.280321`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2549.372075`
- pi_loss_mean: `-178.836513`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `33.974338`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2339.842824`
- pi_loss_mean: `-180.414851`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `24.064820`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2594.635518`
- pi_loss_mean: `-187.042130`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `103.430797`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2682.994516`
- pi_loss_mean: `-187.935553`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `128.924124`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3315.082326`
- pi_loss_mean: `-193.584881`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `36.300034`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2137.968611`
- pi_loss_mean: `-199.608218`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `-19.024548`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4027.842074`
- pi_loss_mean: `-195.204661`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `-12.900588`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1813.608340`
- pi_loss_mean: `-193.832006`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `-24.767853`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1528.290897`
- pi_loss_mean: `-192.302396`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-54.389679`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1979.205101`
- pi_loss_mean: `-186.718692`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-32.087172`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2401.368523`
- pi_loss_mean: `-181.769701`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-20.177885`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1576.682292`
- pi_loss_mean: `-180.527003`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `59.964941`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2138.629096`
- pi_loss_mean: `-176.461840`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `37.523862`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2376.332194`
- pi_loss_mean: `-170.110931`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-67.110508`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1074.321922`
- pi_loss_mean: `-168.004368`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `-17.119884`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1479.788488`
- pi_loss_mean: `-160.909029`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-15.852661`
- steps: `516`

### Eval episode 2

- episode_return: `-15.852661`
- steps: `516`

