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
- created_utc: `2026-06-25T07:31:43.414958+00:00`

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
- q_loss_mean: `17476.182275`
- pi_loss_mean: `-0.129257`
- kl_mean: `3.893064`
- eta_mean: `2.744897`

### Train episode 2

- episode_return: `-2500.000000`
- steps: `25`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `25`
- q_loss_mean: `11057.404487`
- pi_loss_mean: `-0.334320`
- kl_mean: `1181.969675`
- eta_mean: `2.816482`

### Train episode 3

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1973.700369`
- pi_loss_mean: `-0.546452`
- kl_mean: `17780.480109`
- eta_mean: `2.903579`

### Train episode 4

- episode_return: `-2700.000000`
- steps: `27`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `27`
- q_loss_mean: `1204.964161`
- pi_loss_mean: `-0.620729`
- kl_mean: `35132.382668`
- eta_mean: `3.021145`

### Train episode 5

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1025.200186`
- pi_loss_mean: `-0.825652`
- kl_mean: `130626.608347`
- eta_mean: `3.152868`

### Train episode 6

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `943.220716`
- pi_loss_mean: `-0.869652`
- kl_mean: `258935.893914`
- eta_mean: `3.288085`

### Train episode 7

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `919.129449`
- pi_loss_mean: `-0.869694`
- kl_mean: `287482.884868`
- eta_mean: `3.423905`

### Train episode 8

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `791.876009`
- pi_loss_mean: `-0.869859`
- kl_mean: `286511.550164`
- eta_mean: `3.549208`

### Train episode 9

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `803.948583`
- pi_loss_mean: `-0.869763`
- kl_mean: `288751.107730`
- eta_mean: `3.665575`

### Train episode 10

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `720.503967`
- pi_loss_mean: `-0.869902`
- kl_mean: `288350.449836`
- eta_mean: `3.778567`

### Train episode 11

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `661.453814`
- pi_loss_mean: `-0.869759`
- kl_mean: `293964.151316`
- eta_mean: `3.888672`

### Train episode 12

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `655.250466`
- pi_loss_mean: `-0.869778`
- kl_mean: `293944.664474`
- eta_mean: `3.999409`

### Train episode 13

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `684.120557`
- pi_loss_mean: `-0.869715`
- kl_mean: `298375.523026`
- eta_mean: `4.111114`

### Train episode 14

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `622.250548`
- pi_loss_mean: `-0.869704`
- kl_mean: `294096.995888`
- eta_mean: `4.223933`

### Train episode 15

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `668.353484`
- pi_loss_mean: `-0.869846`
- kl_mean: `305019.162829`
- eta_mean: `4.338520`

### Train episode 16

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `661.754881`
- pi_loss_mean: `-0.869812`
- kl_mean: `295319.131579`
- eta_mean: `4.455673`

### Train episode 17

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `605.825775`
- pi_loss_mean: `-0.869821`
- kl_mean: `298697.616776`
- eta_mean: `4.574172`

### Train episode 18

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `711.965179`
- pi_loss_mean: `-0.869742`
- kl_mean: `297377.075658`
- eta_mean: `4.695472`

### Train episode 19

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `794.995005`
- pi_loss_mean: `-0.869760`
- kl_mean: `290004.885691`
- eta_mean: `4.817930`

### Train episode 20

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `776.155222`
- pi_loss_mean: `-0.869795`
- kl_mean: `291006.946546`
- eta_mean: `4.941625`

### Train episode 21

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `844.681535`
- pi_loss_mean: `-0.869879`
- kl_mean: `293619.616776`
- eta_mean: `5.068198`

### Train episode 22

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `890.889183`
- pi_loss_mean: `-0.869829`
- kl_mean: `303565.952303`
- eta_mean: `5.200382`

### Train episode 23

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `845.102129`
- pi_loss_mean: `-0.869876`
- kl_mean: `296365.422697`
- eta_mean: `5.338053`

### Train episode 24

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `913.739149`
- pi_loss_mean: `-0.869811`
- kl_mean: `298572.241776`
- eta_mean: `5.478232`

### Train episode 25

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `980.174888`
- pi_loss_mean: `-0.869819`
- kl_mean: `302334.544408`
- eta_mean: `5.624121`

### Train episode 26

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `945.975223`
- pi_loss_mean: `-0.869848`
- kl_mean: `304717.123355`
- eta_mean: `5.775628`

### Train episode 27

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1104.287071`
- pi_loss_mean: `-0.869808`
- kl_mean: `303987.391447`
- eta_mean: `5.931138`

### Train episode 28

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1094.916281`
- pi_loss_mean: `-0.869896`
- kl_mean: `307495.631579`
- eta_mean: `6.091134`

### Train episode 29

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1112.253283`
- pi_loss_mean: `-0.869765`
- kl_mean: `306669.560855`
- eta_mean: `6.257673`

### Train episode 30

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1244.968278`
- pi_loss_mean: `-0.869863`
- kl_mean: `311712.567434`
- eta_mean: `6.430809`

### Train episode 31

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1320.396899`
- pi_loss_mean: `-0.869825`
- kl_mean: `307067.296053`
- eta_mean: `6.609790`

### Train episode 32

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1370.452723`
- pi_loss_mean: `-0.869829`
- kl_mean: `305582.689145`
- eta_mean: `6.793088`

### Train episode 33

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1220.127535`
- pi_loss_mean: `-0.869819`
- kl_mean: `307806.824013`
- eta_mean: `6.980120`

### Train episode 34

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1370.613371`
- pi_loss_mean: `-0.869731`
- kl_mean: `306554.161184`
- eta_mean: `7.175016`

### Train episode 35

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1522.796316`
- pi_loss_mean: `-0.869845`
- kl_mean: `309893.037829`
- eta_mean: `7.375782`

### Train episode 36

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1920.472251`
- pi_loss_mean: `-0.869802`
- kl_mean: `308082.189145`
- eta_mean: `7.584395`

### Train episode 37

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1738.337283`
- pi_loss_mean: `-0.869720`
- kl_mean: `312660.555921`
- eta_mean: `7.799902`

### Train episode 38

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1791.147339`
- pi_loss_mean: `-0.869873`
- kl_mean: `312342.320724`
- eta_mean: `8.024771`

### Train episode 39

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1780.494712`
- pi_loss_mean: `-0.869748`
- kl_mean: `312316.161184`
- eta_mean: `8.255550`

### Train episode 40

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `1988.499602`
- pi_loss_mean: `-0.869801`
- kl_mean: `316730.078947`
- eta_mean: `8.496286`

### Train episode 41

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2071.902797`
- pi_loss_mean: `-0.869763`
- kl_mean: `312619.546053`
- eta_mean: `8.746457`

### Train episode 42

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2299.221024`
- pi_loss_mean: `-0.869840`
- kl_mean: `300463.879934`
- eta_mean: `9.001211`

### Train episode 43

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2250.656507`
- pi_loss_mean: `-0.869880`
- kl_mean: `309977.807566`
- eta_mean: `9.261637`

### Train episode 44

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2256.253501`
- pi_loss_mean: `-0.869791`
- kl_mean: `328391.504934`
- eta_mean: `9.537228`

### Train episode 45

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2583.704815`
- pi_loss_mean: `-0.869779`
- kl_mean: `321370.100329`
- eta_mean: `9.829763`

### Train episode 46

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2239.956196`
- pi_loss_mean: `-0.869797`
- kl_mean: `325759.738487`
- eta_mean: `10.131850`

### Train episode 47

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2511.196251`
- pi_loss_mean: `-0.869795`
- kl_mean: `316638.919408`
- eta_mean: `10.445656`

### Train episode 48

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2476.875508`
- pi_loss_mean: `-0.869748`
- kl_mean: `321535.064145`
- eta_mean: `10.764767`

### Train episode 49

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2873.109124`
- pi_loss_mean: `-0.869741`
- kl_mean: `307981.668586`
- eta_mean: `11.095367`

### Train episode 50

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `2955.688708`
- pi_loss_mean: `-0.869870`
- kl_mean: `312266.641447`
- eta_mean: `11.432402`

### Train episode 51

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3127.657959`
- pi_loss_mean: `-0.869791`
- kl_mean: `325346.274671`
- eta_mean: `11.783984`

### Train episode 52

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3115.796387`
- pi_loss_mean: `-0.869744`
- kl_mean: `322447.661184`
- eta_mean: `12.158975`

### Train episode 53

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3307.087177`
- pi_loss_mean: `-0.869822`
- kl_mean: `323820.129934`
- eta_mean: `12.546215`

### Train episode 54

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3499.857608`
- pi_loss_mean: `-0.869770`
- kl_mean: `322117.858553`
- eta_mean: `12.947560`

### Train episode 55

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3591.673700`
- pi_loss_mean: `-0.869800`
- kl_mean: `331988.590461`
- eta_mean: `13.363437`

### Train episode 56

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3532.324630`
- pi_loss_mean: `-0.869733`
- kl_mean: `312937.442434`
- eta_mean: `13.793939`

### Train episode 57

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3241.626356`
- pi_loss_mean: `-0.869744`
- kl_mean: `321767.621711`
- eta_mean: `14.232836`

### Train episode 58

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3318.835539`
- pi_loss_mean: `-0.869822`
- kl_mean: `324709.343750`
- eta_mean: `14.696638`

### Train episode 59

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3618.002467`
- pi_loss_mean: `-0.869895`
- kl_mean: `336688.856908`
- eta_mean: `15.180446`

### Train episode 60

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3615.593776`
- pi_loss_mean: `-0.869749`
- kl_mean: `326254.312500`
- eta_mean: `15.691081`

### Train episode 61

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4182.723177`
- pi_loss_mean: `-0.869819`
- kl_mean: `335730.238487`
- eta_mean: `16.217405`

### Train episode 62

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `3902.187995`
- pi_loss_mean: `-0.869759`
- kl_mean: `327106.366776`
- eta_mean: `16.768603`

### Train episode 63

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4947.574797`
- pi_loss_mean: `-0.869804`
- kl_mean: `337920.197368`
- eta_mean: `17.336202`

### Train episode 64

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4045.340171`
- pi_loss_mean: `-0.869820`
- kl_mean: `327328.564145`
- eta_mean: `17.930673`

### Train episode 65

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4841.373895`
- pi_loss_mean: `-0.869751`
- kl_mean: `331767.325658`
- eta_mean: `18.540607`

### Train episode 66

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4862.133249`
- pi_loss_mean: `-0.869799`
- kl_mean: `331089.009868`
- eta_mean: `19.174025`

### Train episode 67

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `4422.701763`
- pi_loss_mean: `-0.869814`
- kl_mean: `315940.600329`
- eta_mean: `19.824482`

### Train episode 68

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5054.000308`
- pi_loss_mean: `-0.869834`
- kl_mean: `330061.986842`
- eta_mean: `20.489633`

### Train episode 69

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5050.015638`
- pi_loss_mean: `-0.869826`
- kl_mean: `329510.379934`
- eta_mean: `21.192713`

### Train episode 70

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5492.713610`
- pi_loss_mean: `-0.869913`
- kl_mean: `343982.585526`
- eta_mean: `21.936647`

### Train episode 71

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6023.394814`
- pi_loss_mean: `-0.869797`
- kl_mean: `333324.264803`
- eta_mean: `22.717014`

### Train episode 72

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5687.908679`
- pi_loss_mean: `-0.869839`
- kl_mean: `334858.832237`
- eta_mean: `23.521004`

### Train episode 73

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5801.465846`
- pi_loss_mean: `-0.869856`
- kl_mean: `344700.511513`
- eta_mean: `24.361588`

### Train episode 74

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5374.822420`
- pi_loss_mean: `-0.869933`
- kl_mean: `338468.236842`
- eta_mean: `25.245797`

### Train episode 75

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5735.689267`
- pi_loss_mean: `-0.869770`
- kl_mean: `336846.246711`
- eta_mean: `26.153424`

### Train episode 76

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5947.895122`
- pi_loss_mean: `-0.869838`
- kl_mean: `341992.495066`
- eta_mean: `27.094665`

### Train episode 77

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6537.289692`
- pi_loss_mean: `-0.869789`
- kl_mean: `342440.585526`
- eta_mean: `28.085213`

### Train episode 78

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `7665.560495`
- pi_loss_mean: `-0.869868`
- kl_mean: `341960.937500`
- eta_mean: `29.112426`

### Train episode 79

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6693.257735`
- pi_loss_mean: `-0.869802`
- kl_mean: `345295.677632`
- eta_mean: `30.178993`

### Train episode 80

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6733.079834`
- pi_loss_mean: `-0.869857`
- kl_mean: `345540.904605`
- eta_mean: `31.295277`

### Train episode 81

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6782.488397`
- pi_loss_mean: `-0.869723`
- kl_mean: `347495.450658`
- eta_mean: `32.468617`

### Train episode 82

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6281.698416`
- pi_loss_mean: `-0.869925`
- kl_mean: `357164.843750`
- eta_mean: `33.687235`

### Train episode 83

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `5476.647962`
- pi_loss_mean: `-0.869836`
- kl_mean: `350020.703947`
- eta_mean: `34.976216`

### Train episode 84

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6788.840782`
- pi_loss_mean: `-0.869859`
- kl_mean: `345737.873355`
- eta_mean: `36.306816`

### Train episode 85

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `7888.060264`
- pi_loss_mean: `-0.869831`
- kl_mean: `350801.986842`
- eta_mean: `37.681470`

### Train episode 86

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `8086.113191`
- pi_loss_mean: `-0.869827`
- kl_mean: `349075.120066`
- eta_mean: `39.105094`

### Train episode 87

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `7735.184056`
- pi_loss_mean: `-0.869707`
- kl_mean: `347587.345395`
- eta_mean: `40.580384`

### Train episode 88

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `7976.240530`
- pi_loss_mean: `-0.869727`
- kl_mean: `350748.050987`
- eta_mean: `42.114391`

### Train episode 89

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `6196.469033`
- pi_loss_mean: `-0.869859`
- kl_mean: `355105.149671`
- eta_mean: `43.732714`

### Train episode 90

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `7950.614900`
- pi_loss_mean: `-0.869845`
- kl_mean: `346248.549342`
- eta_mean: `45.430033`

### Train episode 91

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `8807.324424`
- pi_loss_mean: `-0.869905`
- kl_mean: `357440.952303`
- eta_mean: `47.168457`

### Train episode 92

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `9298.674265`
- pi_loss_mean: `-0.869843`
- kl_mean: `357668.955592`
- eta_mean: `48.997055`

### Train episode 93

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `9387.734928`
- pi_loss_mean: `-0.869969`
- kl_mean: `355565.328947`
- eta_mean: `50.922970`

### Train episode 94

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `8143.504626`
- pi_loss_mean: `-0.869879`
- kl_mean: `370614.745066`
- eta_mean: `52.920476`

### Train episode 95

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `10005.034257`
- pi_loss_mean: `-0.869796`
- kl_mean: `349096.287829`
- eta_mean: `55.032773`

### Train episode 96

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `9941.470035`
- pi_loss_mean: `-0.869818`
- kl_mean: `352788.787829`
- eta_mean: `57.177814`

### Train episode 97

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `9990.132504`
- pi_loss_mean: `-0.869873`
- kl_mean: `351741.148026`
- eta_mean: `59.400302`

### Train episode 98

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `10674.461811`
- pi_loss_mean: `-0.869869`
- kl_mean: `361280.955592`
- eta_mean: `61.718303`

### Train episode 99

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `10538.251169`
- pi_loss_mean: `-0.869810`
- kl_mean: `360421.654605`
- eta_mean: `64.161622`

### Train episode 100

- episode_return: `-1900.000000`
- steps: `19`
- ended_early_on_budget: `True`
- configured_episode_steps: `2903`
- n_train_updates: `19`
- q_loss_mean: `10463.601023`
- pi_loss_mean: `-0.869784`
- kl_mean: `363263.302632`
- eta_mean: `66.717289`

### Eval episode 1

- episode_return: `-262582.304842`
- steps: `2903`

### Eval episode 2

- episode_return: `-262582.304842`
- steps: `2903`

