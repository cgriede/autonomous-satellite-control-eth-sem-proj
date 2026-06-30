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
- created_utc: `2026-06-29T21:41:58.669046+00:00`

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

- episode_return: `-75.890647`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `53.837168`
- pi_loss_mean: `-10.455501`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-11.158844`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `116.952650`
- pi_loss_mean: `-25.017954`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-21.096845`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `173.090885`
- pi_loss_mean: `-36.040296`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-39.562837`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `479.501575`
- pi_loss_mean: `-45.893587`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-29.321333`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `717.003707`
- pi_loss_mean: `-62.527617`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-26.761137`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `566.672046`
- pi_loss_mean: `-72.724815`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-27.288504`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `473.871884`
- pi_loss_mean: `-78.800478`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-27.264813`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `422.428487`
- pi_loss_mean: `-82.166575`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-19.195453`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `419.129163`
- pi_loss_mean: `-86.259751`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-21.426371`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `420.577307`
- pi_loss_mean: `-87.806468`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-22.889750`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `481.591175`
- pi_loss_mean: `-89.159253`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-44.906694`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `486.558181`
- pi_loss_mean: `-89.465636`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-77.335514`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `445.036090`
- pi_loss_mean: `-86.445635`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-76.303086`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `418.183864`
- pi_loss_mean: `-82.113771`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-56.246862`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `366.340778`
- pi_loss_mean: `-78.359150`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-75.418107`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `347.033319`
- pi_loss_mean: `-75.073730`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-73.626987`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `343.797900`
- pi_loss_mean: `-72.420926`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-73.588293`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `280.117812`
- pi_loss_mean: `-69.181363`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-72.928019`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `261.824206`
- pi_loss_mean: `-66.477829`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-71.731532`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `234.052337`
- pi_loss_mean: `-62.372801`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-71.632514`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `244.343293`
- pi_loss_mean: `-61.005479`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-70.442250`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `237.348432`
- pi_loss_mean: `-58.348661`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-37.339684`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `210.873433`
- pi_loss_mean: `-55.545707`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `11.535580`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `217.267953`
- pi_loss_mean: `-56.364349`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `42.204517`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `243.839112`
- pi_loss_mean: `-57.797575`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `18.649574`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `259.415968`
- pi_loss_mean: `-61.893052`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `76.343437`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `255.074609`
- pi_loss_mean: `-65.310118`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `74.605966`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `268.576670`
- pi_loss_mean: `-66.093600`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `35.872832`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `241.397516`
- pi_loss_mean: `-66.212064`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `23.400050`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `234.500210`
- pi_loss_mean: `-66.097677`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `12.348597`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `203.056923`
- pi_loss_mean: `-65.252407`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `5.460691`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `190.314514`
- pi_loss_mean: `-65.301679`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-0.581526`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `179.710055`
- pi_loss_mean: `-66.133683`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `34.374014`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `168.291666`
- pi_loss_mean: `-67.761508`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-28.992667`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `171.934345`
- pi_loss_mean: `-69.107274`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `68.970093`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `173.458965`
- pi_loss_mean: `-70.330009`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `18.027190`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `172.298690`
- pi_loss_mean: `-72.033117`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `-17.917263`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `160.383588`
- pi_loss_mean: `-72.222331`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `125.063618`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `151.303012`
- pi_loss_mean: `-73.284563`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `80.212057`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `136.184249`
- pi_loss_mean: `-73.605959`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `99.016039`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `135.898845`
- pi_loss_mean: `-73.815721`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `22.852197`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `129.065575`
- pi_loss_mean: `-74.085347`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `13.373560`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `125.505369`
- pi_loss_mean: `-72.941136`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `-8.061474`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `119.246341`
- pi_loss_mean: `-71.699850`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-38.578865`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `111.121950`
- pi_loss_mean: `-71.347007`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `-19.203781`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `109.893149`
- pi_loss_mean: `-70.375796`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `-13.251786`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `97.712039`
- pi_loss_mean: `-69.891969`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `-33.485217`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `103.526318`
- pi_loss_mean: `-68.642171`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-8.239717`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `87.481122`
- pi_loss_mean: `-67.581550`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `129.750565`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `79.832227`
- pi_loss_mean: `-66.541523`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `50.571501`
- steps: `516`

### Eval episode 2

- episode_return: `50.571501`
- steps: `516`

