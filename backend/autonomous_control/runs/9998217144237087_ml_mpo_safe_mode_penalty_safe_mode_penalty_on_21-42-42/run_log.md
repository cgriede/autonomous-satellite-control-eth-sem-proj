# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo safe mode penalty`
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
- created_utc: `2026-06-30T21:42:42.914088+00:00`

## Events

### Warmup episode 1 (baseline overflight)

- episode_return: `482.881585`
- steps: `516`

### Warmup episode 2 (baseline overflight)

- episode_return: `417.468337`
- steps: `516`

### Warmup episode 3 (baseline overflight)

- episode_return: `278.995889`
- steps: `516`

### Warmup episode 4 (baseline overflight)

- episode_return: `421.677421`
- steps: `516`

### Warmup episode 5 (baseline overflight)

- episode_return: `449.915993`
- steps: `516`

### Train episode 1

- episode_return: `-1168.324770`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `35.056278`
- pi_loss_mean: `-0.173818`
- kl_mean: `-0.116763`
- eta_mean: `3.132281`

### Train episode 2

- episode_return: `-1219.952754`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `69.100211`
- pi_loss_mean: `-0.242654`
- kl_mean: `-0.064085`
- eta_mean: `4.765338`

### Train episode 3

- episode_return: `-954.762605`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `140.428270`
- pi_loss_mean: `-0.303893`
- kl_mean: `0.000517`
- eta_mean: `5.798293`

### Train episode 4

- episode_return: `-888.120739`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `262.061962`
- pi_loss_mean: `-0.341738`
- kl_mean: `0.034918`
- eta_mean: `4.666755`

### Train episode 5

- episode_return: `-858.147363`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `474.173279`
- pi_loss_mean: `-0.382362`
- kl_mean: `0.035396`
- eta_mean: `3.668631`

### Train episode 6

- episode_return: `-796.101279`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `724.284388`
- pi_loss_mean: `-0.420226`
- kl_mean: `0.029619`
- eta_mean: `2.995708`

### Train episode 7

- episode_return: `-824.632898`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `795.109445`
- pi_loss_mean: `-0.448838`
- kl_mean: `0.022545`
- eta_mean: `2.471462`

### Train episode 8

- episode_return: `-785.962634`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1077.137797`
- pi_loss_mean: `-0.464859`
- kl_mean: `0.013499`
- eta_mean: `2.109359`

### Train episode 9

- episode_return: `-773.636130`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1220.438579`
- pi_loss_mean: `-0.473728`
- kl_mean: `0.010766`
- eta_mean: `2.087845`

### Train episode 10

- episode_return: `-804.627661`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1429.641997`
- pi_loss_mean: `-0.475331`
- kl_mean: `0.018586`
- eta_mean: `2.123619`

### Train episode 11

- episode_return: `-649.404063`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1668.611810`
- pi_loss_mean: `-0.482837`
- kl_mean: `0.017225`
- eta_mean: `1.923279`

### Train episode 12

- episode_return: `-626.415575`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1647.177959`
- pi_loss_mean: `-0.488407`
- kl_mean: `0.014384`
- eta_mean: `1.501362`

### Train episode 13

- episode_return: `-635.354688`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1535.238567`
- pi_loss_mean: `-0.491062`
- kl_mean: `0.012482`
- eta_mean: `1.360504`

### Train episode 14

- episode_return: `-663.250927`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1714.575002`
- pi_loss_mean: `-0.490194`
- kl_mean: `0.017100`
- eta_mean: `1.459913`

### Train episode 15

- episode_return: `-496.327505`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1710.423744`
- pi_loss_mean: `-0.490073`
- kl_mean: `0.022788`
- eta_mean: `1.644231`

### Train episode 16

- episode_return: `-661.778806`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2244.028391`
- pi_loss_mean: `-0.492546`
- kl_mean: `0.019402`
- eta_mean: `1.421030`

### Train episode 17

- episode_return: `-806.995972`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2348.783957`
- pi_loss_mean: `-0.495287`
- kl_mean: `0.016906`
- eta_mean: `1.200292`

### Train episode 18

- episode_return: `-621.804271`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2440.839621`
- pi_loss_mean: `-0.494901`
- kl_mean: `0.018451`
- eta_mean: `1.055980`

### Train episode 19

- episode_return: `-786.921728`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2208.209487`
- pi_loss_mean: `-0.494652`
- kl_mean: `0.020333`
- eta_mean: `1.057261`

### Train episode 20

- episode_return: `-640.940539`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3338.993730`
- pi_loss_mean: `-0.492571`
- kl_mean: `0.022737`
- eta_mean: `1.134164`

### Train episode 21

- episode_return: `-646.838202`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2516.326340`
- pi_loss_mean: `-0.492112`
- kl_mean: `0.019673`
- eta_mean: `1.239094`

### Train episode 22

- episode_return: `-492.383039`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2835.053750`
- pi_loss_mean: `-0.490138`
- kl_mean: `0.023041`
- eta_mean: `1.521131`

### Train episode 23

- episode_return: `-502.074725`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2607.927863`
- pi_loss_mean: `-0.491881`
- kl_mean: `0.019342`
- eta_mean: `1.758245`

### Train episode 24

- episode_return: `-354.411409`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3438.365706`
- pi_loss_mean: `-0.493384`
- kl_mean: `0.018624`
- eta_mean: `1.603273`

### Train episode 25

- episode_return: `-642.316249`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3198.015983`
- pi_loss_mean: `-0.496106`
- kl_mean: `0.019056`
- eta_mean: `1.323755`

### Train episode 26

- episode_return: `-488.856350`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5758.019943`
- pi_loss_mean: `-0.498157`
- kl_mean: `0.018014`
- eta_mean: `1.003673`

### Train episode 27

- episode_return: `-676.604764`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5127.234079`
- pi_loss_mean: `-0.499187`
- kl_mean: `0.020923`
- eta_mean: `0.771124`

### Train episode 28

- episode_return: `-654.669934`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3224.437929`
- pi_loss_mean: `-0.497962`
- kl_mean: `0.020926`
- eta_mean: `0.653120`

### Train episode 29

- episode_return: `-817.297743`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5330.399927`
- pi_loss_mean: `-0.497782`
- kl_mean: `0.020031`
- eta_mean: `0.592508`

### Train episode 30

- episode_return: `-812.695662`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7558.224117`
- pi_loss_mean: `-0.498576`
- kl_mean: `0.019072`
- eta_mean: `0.535860`

### Train episode 31

- episode_return: `-658.736677`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2311.637869`
- pi_loss_mean: `-0.494746`
- kl_mean: `0.022728`
- eta_mean: `0.575215`

### Train episode 32

- episode_return: `-825.041856`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `8224.217468`
- pi_loss_mean: `-0.493720`
- kl_mean: `0.020443`
- eta_mean: `0.760927`

### Train episode 33

- episode_return: `-632.506266`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4143.745067`
- pi_loss_mean: `-0.493551`
- kl_mean: `0.021081`
- eta_mean: `0.946848`

### Train episode 34

- episode_return: `-792.197484`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5405.217921`
- pi_loss_mean: `-0.493218`
- kl_mean: `0.019892`
- eta_mean: `1.162458`

### Train episode 35

- episode_return: `-648.537719`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6096.907029`
- pi_loss_mean: `-0.494203`
- kl_mean: `0.019235`
- eta_mean: `1.193415`

### Train episode 36

- episode_return: `-482.682534`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `7598.521053`
- pi_loss_mean: `-0.493601`
- kl_mean: `0.019879`
- eta_mean: `1.172240`

### Train episode 37

- episode_return: `-641.132348`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2743.571250`
- pi_loss_mean: `-0.493093`
- kl_mean: `0.020033`
- eta_mean: `1.272585`

### Train episode 38

- episode_return: `-518.628247`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3074.425475`
- pi_loss_mean: `-0.492450`
- kl_mean: `0.020794`
- eta_mean: `1.374978`

### Train episode 39

- episode_return: `-644.413519`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `4104.330814`
- pi_loss_mean: `-0.492236`
- kl_mean: `0.019620`
- eta_mean: `1.510927`

### Train episode 40

- episode_return: `-644.862454`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5382.589966`
- pi_loss_mean: `-0.493016`
- kl_mean: `0.019930`
- eta_mean: `1.501335`

### Train episode 41

- episode_return: `-662.922206`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5492.886767`
- pi_loss_mean: `-0.494375`
- kl_mean: `0.018861`
- eta_mean: `1.339982`

### Train episode 42

- episode_return: `-493.226063`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3431.645038`
- pi_loss_mean: `-0.494511`
- kl_mean: `0.018855`
- eta_mean: `1.224983`

### Train episode 43

- episode_return: `-668.682955`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3759.371134`
- pi_loss_mean: `-0.495082`
- kl_mean: `0.020447`
- eta_mean: `1.071459`

### Train episode 44

- episode_return: `-485.063398`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3169.427226`
- pi_loss_mean: `-0.494733`
- kl_mean: `0.020244`
- eta_mean: `0.987259`

### Train episode 45

- episode_return: `-651.385012`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3921.197956`
- pi_loss_mean: `-0.494970`
- kl_mean: `0.018840`
- eta_mean: `0.939955`

### Train episode 46

- episode_return: `-670.763595`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3662.699297`
- pi_loss_mean: `-0.493879`
- kl_mean: `0.020680`
- eta_mean: `0.904584`

### Train episode 47

- episode_return: `-650.938260`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2756.605626`
- pi_loss_mean: `-0.492609`
- kl_mean: `0.019635`
- eta_mean: `0.947120`

### Train episode 48

- episode_return: `-677.175593`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2168.756934`
- pi_loss_mean: `-0.492238`
- kl_mean: `0.020034`
- eta_mean: `0.856284`

### Train episode 49

- episode_return: `-663.016078`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1626.631446`
- pi_loss_mean: `-0.490233`
- kl_mean: `0.022575`
- eta_mean: `0.816357`

### Train episode 50

- episode_return: `-512.553459`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `5348.391655`
- pi_loss_mean: `-0.489768`
- kl_mean: `0.019351`
- eta_mean: `0.918623`

### Eval episode 1

- episode_return: `-510.405238`
- steps: `516`

### Eval episode 2

- episode_return: `-510.405238`
- steps: `516`

