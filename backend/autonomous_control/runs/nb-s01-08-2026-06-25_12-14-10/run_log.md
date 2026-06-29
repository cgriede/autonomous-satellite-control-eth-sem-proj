# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- warmup_episodes: `4`
- train_episodes: `100`
- eval_episodes: `2`
- scalar_dim: `3`
- vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- vision_seq_lens: `[100, 200]`
- encoder_output_dim: `180`
- code_embed_dim: `8`
- cnn_embedding_dim: `32`
- feature_attitude_keys: `['body_z_angle_rad', 'omega_sat_rad_s']`
- feature_orbit_keys: `['theta_orbit_rad']`
- feature_vision_keys: `['camera_observation_line_codes', 'secondary_camera_observation_line_codes']`
- sampled_altitude_km: `528.7583065070219`
- created_utc: `2026-06-25T12:14:10.592723+00:00`

## Events

### Warmup episode 1 (random)

- episode_return: `-270775.792411`
- steps: `2903`

### Warmup episode 2 (random)

- episode_return: `-258084.696795`
- steps: `2903`

### Warmup episode 3 (baseline)

- episode_return: `-258772.704243`
- steps: `2903`

### Warmup episode 4 (baseline)

- episode_return: `-258772.704243`
- steps: `2903`

### Train episode 1

- episode_return: `-2900.000000`
- steps: `29`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `29`
- q_loss_mean: `17010.079371`
- pi_loss_mean: `-0.166488`
- kl_mean: `15.829509`
- eta_mean: `2.758373`

### Train episode 2

- episode_return: `-3100.000000`
- steps: `31`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `31`
- q_loss_mean: `5341.115660`
- pi_loss_mean: `-0.458504`
- kl_mean: `8492.270358`
- eta_mean: `2.861510`

### Train episode 3

- episode_return: `-2100.000000`
- steps: `21`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `21`
- q_loss_mean: `1337.117798`
- pi_loss_mean: `-0.588746`
- kl_mean: `29811.890160`
- eta_mean: `2.983659`

### Train episode 4

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1098.698316`
- pi_loss_mean: `-0.733236`
- kl_mean: `63271.355880`
- eta_mean: `3.092754`

### Train episode 5

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `973.861971`
- pi_loss_mean: `-0.866475`
- kl_mean: `201307.609375`
- eta_mean: `3.216552`

### Train episode 6

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `951.594081`
- pi_loss_mean: `-0.869764`
- kl_mean: `260948.576480`
- eta_mean: `3.354313`

### Train episode 7

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `847.126115`
- pi_loss_mean: `-0.869736`
- kl_mean: `275245.391447`
- eta_mean: `3.484766`

### Train episode 8

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `829.108537`
- pi_loss_mean: `-0.869778`
- kl_mean: `278975.465461`
- eta_mean: `3.606350`

### Train episode 9

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `732.885803`
- pi_loss_mean: `-0.869869`
- kl_mean: `285077.946546`
- eta_mean: `3.722368`

### Train episode 10

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `682.267607`
- pi_loss_mean: `-0.869738`
- kl_mean: `281104.465461`
- eta_mean: `3.835889`

### Train episode 11

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `640.614806`
- pi_loss_mean: `-0.869741`
- kl_mean: `272316.192434`
- eta_mean: `3.946237`

### Train episode 12

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `724.824434`
- pi_loss_mean: `-0.869757`
- kl_mean: `278840.528783`
- eta_mean: `4.055089`

### Train episode 13

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `619.770003`
- pi_loss_mean: `-0.869799`
- kl_mean: `282061.851974`
- eta_mean: `4.165927`

### Train episode 14

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `645.127828`
- pi_loss_mean: `-0.869802`
- kl_mean: `296432.320724`
- eta_mean: `4.279958`

### Train episode 15

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `698.744237`
- pi_loss_mean: `-0.869835`
- kl_mean: `278332.194079`
- eta_mean: `4.397236`

### Train episode 16

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `598.635288`
- pi_loss_mean: `-0.869857`
- kl_mean: `280275.413651`
- eta_mean: `4.513172`

### Train episode 17

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `630.925502`
- pi_loss_mean: `-0.869876`
- kl_mean: `289931.618421`
- eta_mean: `4.631415`

### Train episode 18

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `784.701702`
- pi_loss_mean: `-0.869871`
- kl_mean: `281125.037007`
- eta_mean: `4.753502`

### Train episode 19

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `786.800042`
- pi_loss_mean: `-0.869941`
- kl_mean: `286467.476151`
- eta_mean: `4.878194`

### Train episode 20

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `833.199052`
- pi_loss_mean: `-0.869861`
- kl_mean: `295455.764803`
- eta_mean: `5.007561`

### Train episode 21

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `861.655893`
- pi_loss_mean: `-0.869725`
- kl_mean: `283124.165296`
- eta_mean: `5.142037`

### Train episode 22

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `841.234144`
- pi_loss_mean: `-0.869886`
- kl_mean: `292596.231086`
- eta_mean: `5.277849`

### Train episode 23

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `876.398296`
- pi_loss_mean: `-0.869896`
- kl_mean: `296970.039474`
- eta_mean: `5.417929`

### Train episode 24

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `961.241603`
- pi_loss_mean: `-0.869778`
- kl_mean: `288123.489309`
- eta_mean: `5.564398`

### Train episode 25

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `875.077900`
- pi_loss_mean: `-0.869922`
- kl_mean: `286931.183388`
- eta_mean: `5.710980`

### Train episode 26

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1097.781006`
- pi_loss_mean: `-0.869696`
- kl_mean: `291999.699836`
- eta_mean: `5.863508`

### Train episode 27

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1081.475226`
- pi_loss_mean: `-0.869874`
- kl_mean: `299236.808388`
- eta_mean: `6.022823`

### Train episode 28

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1077.566401`
- pi_loss_mean: `-0.869842`
- kl_mean: `290626.708882`
- eta_mean: `6.186635`

### Train episode 29

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1149.864415`
- pi_loss_mean: `-0.869866`
- kl_mean: `298829.692434`
- eta_mean: `6.355224`

### Train episode 30

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1229.961101`
- pi_loss_mean: `-0.869855`
- kl_mean: `295851.620066`
- eta_mean: `6.530760`

### Train episode 31

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1271.714879`
- pi_loss_mean: `-0.869835`
- kl_mean: `298931.782895`
- eta_mean: `6.711320`

### Train episode 32

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1249.502910`
- pi_loss_mean: `-0.869859`
- kl_mean: `296512.850329`
- eta_mean: `6.898075`

### Train episode 33

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1247.440320`
- pi_loss_mean: `-0.869827`
- kl_mean: `309196.985197`
- eta_mean: `7.092421`

### Train episode 34

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1482.647509`
- pi_loss_mean: `-0.869846`
- kl_mean: `302206.555921`
- eta_mean: `7.296469`

### Train episode 35

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1582.174387`
- pi_loss_mean: `-0.869757`
- kl_mean: `305617.490132`
- eta_mean: `7.506087`

### Train episode 36

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1999.863744`
- pi_loss_mean: `-0.869697`
- kl_mean: `306183.604441`
- eta_mean: `7.721626`

### Train episode 37

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1693.423905`
- pi_loss_mean: `-0.869894`
- kl_mean: `304143.074013`
- eta_mean: `7.945699`

### Train episode 38

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1754.363753`
- pi_loss_mean: `-0.869797`
- kl_mean: `316347.750000`
- eta_mean: `8.178481`

### Train episode 39

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1995.784128`
- pi_loss_mean: `-0.869766`
- kl_mean: `308407.442434`
- eta_mean: `8.421505`

### Train episode 40

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1836.480173`
- pi_loss_mean: `-0.869786`
- kl_mean: `303308.703125`
- eta_mean: `8.670254`

### Train episode 41

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2338.916446`
- pi_loss_mean: `-0.869892`
- kl_mean: `305939.633224`
- eta_mean: `8.926324`

### Train episode 42

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2494.678994`
- pi_loss_mean: `-0.869852`
- kl_mean: `310652.680921`
- eta_mean: `9.189570`

### Train episode 43

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2215.022345`
- pi_loss_mean: `-0.869842`
- kl_mean: `306154.603618`
- eta_mean: `9.464731`

