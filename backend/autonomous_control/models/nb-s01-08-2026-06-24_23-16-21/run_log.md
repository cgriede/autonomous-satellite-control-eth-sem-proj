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
- created_utc: `2026-06-24T23:16:21.967333+00:00`

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

- episode_return: `-2300.000000`
- steps: `23`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `20`
- q_loss_mean: `17476.178613`
- pi_loss_mean: `-0.129257`
- kl_mean: `3.892487`
- eta_mean: `2.744897`

### Train episode 2

- episode_return: `-2500.000000`
- steps: `25`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `25`
- q_loss_mean: `11057.438828`
- pi_loss_mean: `-0.334310`
- kl_mean: `1181.441280`
- eta_mean: `2.816483`

### Train episode 3

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1974.015175`
- pi_loss_mean: `-0.546443`
- kl_mean: `17776.544254`
- eta_mean: `2.903579`

### Train episode 4

- episode_return: `-2700.000000`
- steps: `27`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `27`
- q_loss_mean: `1204.917345`
- pi_loss_mean: `-0.620695`
- kl_mean: `35104.481698`
- eta_mean: `3.021144`

### Train episode 5

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1025.337736`
- pi_loss_mean: `-0.825592`
- kl_mean: `130393.401316`
- eta_mean: `3.152836`

### Train episode 6

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `943.167259`
- pi_loss_mean: `-0.869653`
- kl_mean: `258787.800164`
- eta_mean: `3.288046`

### Train episode 7

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `918.222984`
- pi_loss_mean: `-0.869694`
- kl_mean: `287348.312500`
- eta_mean: `3.423890`

### Train episode 8

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `791.302638`
- pi_loss_mean: `-0.869859`
- kl_mean: `286391.573191`
- eta_mean: `3.549215`

### Train episode 9

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `803.392202`
- pi_loss_mean: `-0.869763`
- kl_mean: `288582.664474`
- eta_mean: `3.665596`

### Train episode 10

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `718.979431`
- pi_loss_mean: `-0.869902`
- kl_mean: `288207.490954`
- eta_mean: `3.778591`

### Train episode 11

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `659.786301`
- pi_loss_mean: `-0.869759`
- kl_mean: `293837.558388`
- eta_mean: `3.888702`

### Train episode 12

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `655.071249`
- pi_loss_mean: `-0.869778`
- kl_mean: `293779.683388`
- eta_mean: `3.999446`

### Train episode 13

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `683.276020`
- pi_loss_mean: `-0.869715`
- kl_mean: `298212.258224`
- eta_mean: `4.111153`

### Train episode 14

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `621.871837`
- pi_loss_mean: `-0.869704`
- kl_mean: `293895.731086`
- eta_mean: `4.223968`

### Train episode 15

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `668.950573`
- pi_loss_mean: `-0.869845`
- kl_mean: `304799.761513`
- eta_mean: `4.338540`

### Train episode 16

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `660.294098`
- pi_loss_mean: `-0.869812`
- kl_mean: `294977.740132`
- eta_mean: `4.455670`

### Train episode 17

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `604.659678`
- pi_loss_mean: `-0.869821`
- kl_mean: `298302.961349`
- eta_mean: `4.574112`

### Train episode 18

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `713.615989`
- pi_loss_mean: `-0.869742`
- kl_mean: `297027.495888`
- eta_mean: `4.695346`

### Train episode 19

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `799.842497`
- pi_loss_mean: `-0.869760`
- kl_mean: `289638.797697`
- eta_mean: `4.817744`

### Train episode 20

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `776.084084`
- pi_loss_mean: `-0.869795`
- kl_mean: `290714.044408`
- eta_mean: `4.941384`

### Train episode 21

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `844.209209`
- pi_loss_mean: `-0.869879`
- kl_mean: `293310.621711`
- eta_mean: `5.067921`

### Train episode 22

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `891.268269`
- pi_loss_mean: `-0.869829`
- kl_mean: `303211.248355`
- eta_mean: `5.200064`

### Train episode 23

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `843.573835`
- pi_loss_mean: `-0.869876`
- kl_mean: `296007.879112`
- eta_mean: `5.337688`

### Train episode 24

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `916.257334`
- pi_loss_mean: `-0.869811`
- kl_mean: `298228.088816`
- eta_mean: `5.477816`

### Train episode 25

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `988.664088`
- pi_loss_mean: `-0.869819`
- kl_mean: `302000.822368`
- eta_mean: `5.623656`

### Train episode 26

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `955.847473`
- pi_loss_mean: `-0.869848`
- kl_mean: `304427.231908`
- eta_mean: `5.775126`

### Train episode 27

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1121.068186`
- pi_loss_mean: `-0.869808`
- kl_mean: `303694.963816`
- eta_mean: `5.930613`

### Train episode 28

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1110.104640`
- pi_loss_mean: `-0.869896`
- kl_mean: `307196.560855`
- eta_mean: `6.090589`

### Train episode 29

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1126.246733`
- pi_loss_mean: `-0.869765`
- kl_mean: `306358.858553`
- eta_mean: `6.257102`

### Train episode 30

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1267.792795`
- pi_loss_mean: `-0.869863`
- kl_mean: `311408.220395`
- eta_mean: `6.430213`

### Train episode 31

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1341.546525`
- pi_loss_mean: `-0.869825`
- kl_mean: `306748.703947`
- eta_mean: `6.609167`

### Train episode 32

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1384.646298`
- pi_loss_mean: `-0.869830`
- kl_mean: `305269.447368`
- eta_mean: `6.792434`

### Train episode 33

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1237.071835`
- pi_loss_mean: `-0.869819`
- kl_mean: `307491.235197`
- eta_mean: `6.979434`

### Train episode 34

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1375.947285`
- pi_loss_mean: `-0.869731`
- kl_mean: `306207.909539`
- eta_mean: `7.174293`

### Train episode 35

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1537.872282`
- pi_loss_mean: `-0.869845`
- kl_mean: `309559.944079`
- eta_mean: `7.375010`

### Train episode 36

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1933.550884`
- pi_loss_mean: `-0.869802`
- kl_mean: `307878.432566`
- eta_mean: `7.583594`

### Train episode 37

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1753.979801`
- pi_loss_mean: `-0.869720`
- kl_mean: `312401.361842`
- eta_mean: `7.799124`

### Train episode 38

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1801.382131`
- pi_loss_mean: `-0.869873`
- kl_mean: `312044.577303`
- eta_mean: `8.023995`

### Train episode 39

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1786.892398`
- pi_loss_mean: `-0.869748`
- kl_mean: `312010.126645`
- eta_mean: `8.254753`

### Train episode 40

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1992.802034`
- pi_loss_mean: `-0.869801`
- kl_mean: `316443.531250`
- eta_mean: `8.495468`

### Train episode 41

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2077.481522`
- pi_loss_mean: `-0.869763`
- kl_mean: `312387.296053`
- eta_mean: `8.745631`

### Train episode 42

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2296.479723`
- pi_loss_mean: `-0.869840`
- kl_mean: `300271.712171`
- eta_mean: `9.000410`

### Train episode 43

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2250.440231`
- pi_loss_mean: `-0.869880`
- kl_mean: `309764.779605`
- eta_mean: `9.260874`

### Train episode 44

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2255.383333`
- pi_loss_mean: `-0.869792`
- kl_mean: `328130.542763`
- eta_mean: `9.536495`

### Train episode 45

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2581.050030`
- pi_loss_mean: `-0.869779`
- kl_mean: `321125.200658`
- eta_mean: `9.829042`

### Train episode 46

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2234.218834`
- pi_loss_mean: `-0.869798`
- kl_mean: `325511.947368`
- eta_mean: `10.131147`

### Train episode 47

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2500.373040`
- pi_loss_mean: `-0.869795`
- kl_mean: `316416.939145`
- eta_mean: `10.444972`

### Train episode 48

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2474.045552`
- pi_loss_mean: `-0.869748`
- kl_mean: `321312.337171`
- eta_mean: `10.764113`

### Train episode 49

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2842.110930`
- pi_loss_mean: `-0.869741`
- kl_mean: `307764.610197`
- eta_mean: `11.094743`

### Train episode 50

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2939.414371`
- pi_loss_mean: `-0.869870`
- kl_mean: `312058.973684`
- eta_mean: `11.431811`

### Train episode 51

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3132.711323`
- pi_loss_mean: `-0.869791`
- kl_mean: `325123.386513`
- eta_mean: `11.783436`

### Train episode 52

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3116.724012`
- pi_loss_mean: `-0.869744`
- kl_mean: `322223.952303`
- eta_mean: `12.158470`

### Train episode 53

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3301.832764`
- pi_loss_mean: `-0.869822`
- kl_mean: `323614.577303`
- eta_mean: `12.545746`

### Train episode 54

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3489.749377`
- pi_loss_mean: `-0.869770`
- kl_mean: `321931.774671`
- eta_mean: `12.947153`

### Train episode 55

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3540.316972`
- pi_loss_mean: `-0.869800`
- kl_mean: `331793.212171`
- eta_mean: `13.363103`

### Train episode 56

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3467.619790`
- pi_loss_mean: `-0.869733`
- kl_mean: `312724.189145`
- eta_mean: `13.793686`

### Train episode 57

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3187.691181`
- pi_loss_mean: `-0.869744`
- kl_mean: `321553.335526`
- eta_mean: `14.232634`

### Train episode 58

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3268.785118`
- pi_loss_mean: `-0.869822`
- kl_mean: `324455.363487`
- eta_mean: `14.696479`

### Train episode 59

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3568.325774`
- pi_loss_mean: `-0.869895`
- kl_mean: `336381.671053`
- eta_mean: `15.180280`

### Train episode 60

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3550.086310`
- pi_loss_mean: `-0.869749`
- kl_mean: `325951.689145`
- eta_mean: `15.690860`

### Train episode 61

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4110.714959`
- pi_loss_mean: `-0.869819`
- kl_mean: `335410.351974`
- eta_mean: `16.217106`

### Train episode 62

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3868.163600`
- pi_loss_mean: `-0.869759`
- kl_mean: `326832.799342`
- eta_mean: `16.768228`

### Train episode 63

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4832.084087`
- pi_loss_mean: `-0.869804`
- kl_mean: `337627.661184`
- eta_mean: `17.335788`

### Train episode 64

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3992.732165`
- pi_loss_mean: `-0.869820`
- kl_mean: `327039.240132`
- eta_mean: `17.930211`

### Train episode 65

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4745.777382`
- pi_loss_mean: `-0.869751`
- kl_mean: `331446.750000`
- eta_mean: `18.540075`

### Train episode 66

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4845.357666`
- pi_loss_mean: `-0.869799`
- kl_mean: `330768.098684`
- eta_mean: `19.173392`

### Train episode 67

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4387.042416`
- pi_loss_mean: `-0.869814`
- kl_mean: `315642.115132`
- eta_mean: `19.823726`

### Train episode 68

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4968.501401`
- pi_loss_mean: `-0.869834`
- kl_mean: `329773.687500`
- eta_mean: `20.488788`

### Train episode 69

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4919.013004`
- pi_loss_mean: `-0.869826`
- kl_mean: `329243.327303`
- eta_mean: `21.191827`

### Train episode 70

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5334.144557`
- pi_loss_mean: `-0.869913`
- kl_mean: `343725.527961`
- eta_mean: `21.935754`

### Train episode 71

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5894.279618`
- pi_loss_mean: `-0.869797`
- kl_mean: `333048.544408`
- eta_mean: `22.716132`

### Train episode 72

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5614.766113`
- pi_loss_mean: `-0.869839`
- kl_mean: `334594.052632`
- eta_mean: `23.520121`

