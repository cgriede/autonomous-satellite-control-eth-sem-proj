# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo vector torque effort`
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
- created_utc: `2026-06-30T22:45:02.209918+00:00`

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

- episode_return: `-700.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.124941`
- pi_loss_mean: `-0.170405`
- kl_mean: `-0.121854`
- eta_mean: `2.198125`

### Train episode 2

- episode_return: `-570.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.125194`
- pi_loss_mean: `-0.226786`
- kl_mean: `-0.071746`
- eta_mean: `1.627611`

### Train episode 3

- episode_return: `-315.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.105525`
- pi_loss_mean: `-0.283565`
- kl_mean: `-0.007370`
- eta_mean: `1.289752`

### Train episode 4

- episode_return: `-150.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.111796`
- pi_loss_mean: `-0.320881`
- kl_mean: `0.028734`
- eta_mean: `0.920251`

### Train episode 5

- episode_return: `-20.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.101315`
- pi_loss_mean: `-0.376046`
- kl_mean: `0.037871`
- eta_mean: `0.627360`

### Train episode 6

- episode_return: `-4.187787`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.101169`
- pi_loss_mean: `-0.430707`
- kl_mean: `0.029348`
- eta_mean: `0.441757`

### Train episode 7

- episode_return: `0.361441`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.103507`
- pi_loss_mean: `-0.466511`
- kl_mean: `0.017495`
- eta_mean: `0.324066`

### Train episode 8

- episode_return: `0.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.095386`
- pi_loss_mean: `-0.486370`
- kl_mean: `0.010642`
- eta_mean: `0.245803`

### Train episode 9

- episode_return: `22.291083`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.141803`
- pi_loss_mean: `-0.494767`
- kl_mean: `0.007668`
- eta_mean: `0.193166`

### Train episode 10

- episode_return: `22.061774`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.153664`
- pi_loss_mean: `-0.494749`
- kl_mean: `0.014551`
- eta_mean: `0.170300`

### Train episode 11

- episode_return: `12.000480`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.128351`
- pi_loss_mean: `-0.498536`
- kl_mean: `0.011609`
- eta_mean: `0.152593`

### Train episode 12

- episode_return: `1.062805`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.190546`
- pi_loss_mean: `-0.500678`
- kl_mean: `0.014249`
- eta_mean: `0.136433`

### Train episode 13

- episode_return: `23.061481`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.310063`
- pi_loss_mean: `-0.505227`
- kl_mean: `0.008444`
- eta_mean: `0.111963`

### Train episode 14

- episode_return: `45.862112`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.367146`
- pi_loss_mean: `-0.504372`
- kl_mean: `0.016201`
- eta_mean: `0.092017`

### Train episode 15

- episode_return: `38.645313`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.527942`
- pi_loss_mean: `-0.501336`
- kl_mean: `0.023594`
- eta_mean: `0.084530`

### Train episode 16

- episode_return: `-33.513828`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.721470`
- pi_loss_mean: `-0.501957`
- kl_mean: `0.016270`
- eta_mean: `0.081883`

### Train episode 17

- episode_return: `-26.187367`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.813026`
- pi_loss_mean: `-0.503383`
- kl_mean: `0.013020`
- eta_mean: `0.077512`

### Train episode 18

- episode_return: `-9.326604`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.986440`
- pi_loss_mean: `-0.503512`
- kl_mean: `0.017889`
- eta_mean: `0.073519`

### Train episode 19

- episode_return: `-134.290086`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.162614`
- pi_loss_mean: `-0.504736`
- kl_mean: `0.017015`
- eta_mean: `0.068464`

### Train episode 20

- episode_return: `13.659291`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.106901`
- pi_loss_mean: `-0.504702`
- kl_mean: `0.017197`
- eta_mean: `0.062273`

### Train episode 21

- episode_return: `75.597088`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.196794`
- pi_loss_mean: `-0.503811`
- kl_mean: `0.021819`
- eta_mean: `0.057857`

### Train episode 22

- episode_return: `20.369651`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.185912`
- pi_loss_mean: `-0.502232`
- kl_mean: `0.025883`
- eta_mean: `0.059481`

### Train episode 23

- episode_return: `29.865321`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.328043`
- pi_loss_mean: `-0.498419`
- kl_mean: `0.030888`
- eta_mean: `0.071735`

### Train episode 24

- episode_return: `35.992570`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.374949`
- pi_loss_mean: `-0.495805`
- kl_mean: `0.024788`
- eta_mean: `0.094320`

### Train episode 25

- episode_return: `15.961517`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.340614`
- pi_loss_mean: `-0.496196`
- kl_mean: `0.021123`
- eta_mean: `0.112217`

### Train episode 26

- episode_return: `31.123582`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.305036`
- pi_loss_mean: `-0.499677`
- kl_mean: `0.015216`
- eta_mean: `0.100919`

### Train episode 27

- episode_return: `16.770728`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.469491`
- pi_loss_mean: `-0.498401`
- kl_mean: `0.025186`
- eta_mean: `0.089147`

### Train episode 28

- episode_return: `27.469370`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.469912`
- pi_loss_mean: `-0.501218`
- kl_mean: `0.016919`
- eta_mean: `0.086572`

### Train episode 29

- episode_return: `17.403372`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.422660`
- pi_loss_mean: `-0.503719`
- kl_mean: `0.015474`
- eta_mean: `0.068929`

### Train episode 30

- episode_return: `33.593445`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.551507`
- pi_loss_mean: `-0.504426`
- kl_mean: `0.016557`
- eta_mean: `0.057929`

### Train episode 31

- episode_return: `16.770728`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.949105`
- pi_loss_mean: `-0.505083`
- kl_mean: `0.017291`
- eta_mean: `0.050768`

### Train episode 32

- episode_return: `16.770728`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.635096`
- pi_loss_mean: `-0.505196`
- kl_mean: `0.019616`
- eta_mean: `0.043806`

### Train episode 33

- episode_return: `20.071267`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.895397`
- pi_loss_mean: `-0.504097`
- kl_mean: `0.023510`
- eta_mean: `0.040036`

### Train episode 34

- episode_return: `21.739406`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.337344`
- pi_loss_mean: `-0.505794`
- kl_mean: `0.016873`
- eta_mean: `0.036072`

### Train episode 35

- episode_return: `35.732442`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.265661`
- pi_loss_mean: `-0.503569`
- kl_mean: `0.029333`
- eta_mean: `0.034038`

### Train episode 36

- episode_return: `31.359674`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.847462`
- pi_loss_mean: `-0.504544`
- kl_mean: `0.019560`
- eta_mean: `0.031327`

### Train episode 37

- episode_return: `0.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.566361`
- pi_loss_mean: `-0.503729`
- kl_mean: `0.018796`
- eta_mean: `0.032466`

### Train episode 38

- episode_return: `14.249239`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.483994`
- pi_loss_mean: `-0.504099`
- kl_mean: `0.021925`
- eta_mean: `0.034533`

### Train episode 39

- episode_return: `20.723332`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.236376`
- pi_loss_mean: `-0.504024`
- kl_mean: `0.021933`
- eta_mean: `0.033927`

### Train episode 40

- episode_return: `31.196742`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.329927`
- pi_loss_mean: `-0.505365`
- kl_mean: `0.016219`
- eta_mean: `0.034325`

### Train episode 41

- episode_return: `28.213281`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.112795`
- pi_loss_mean: `-0.506501`
- kl_mean: `0.011567`
- eta_mean: `0.031875`

### Train episode 42

- episode_return: `0.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.696391`
- pi_loss_mean: `-0.505945`
- kl_mean: `0.015821`
- eta_mean: `0.031186`

### Train episode 43

- episode_return: `0.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.379422`
- pi_loss_mean: `-0.502475`
- kl_mean: `0.028404`
- eta_mean: `0.039091`

### Train episode 44

- episode_return: `0.000000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.131541`
- pi_loss_mean: `-0.503395`
- kl_mean: `0.021324`
- eta_mean: `0.048698`

### Train episode 45

- episode_return: `23.392367`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.996155`
- pi_loss_mean: `-0.503700`
- kl_mean: `0.020190`
- eta_mean: `0.049780`

### Train episode 46

- episode_return: `17.990698`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.122756`
- pi_loss_mean: `-0.504154`
- kl_mean: `0.021265`
- eta_mean: `0.050602`

### Train episode 47

- episode_return: `61.362308`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.322817`
- pi_loss_mean: `-0.503015`
- kl_mean: `0.022630`
- eta_mean: `0.048274`

### Train episode 48

- episode_return: `33.593445`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.652436`
- pi_loss_mean: `-0.504071`
- kl_mean: `0.019515`
- eta_mean: `0.043670`

### Train episode 49

- episode_return: `25.253861`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.163711`
- pi_loss_mean: `-0.505059`
- kl_mean: `0.019669`
- eta_mean: `0.036296`

### Train episode 50

- episode_return: `16.770728`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2.028558`
- pi_loss_mean: `-0.505633`
- kl_mean: `0.018182`
- eta_mean: `0.029959`

### Eval episode 1

- episode_return: `25.253861`
- steps: `516`

### Eval episode 2

- episode_return: `25.253861`
- steps: `516`

