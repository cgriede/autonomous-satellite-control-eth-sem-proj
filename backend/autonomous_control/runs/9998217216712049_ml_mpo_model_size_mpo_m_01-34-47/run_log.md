# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `mpo model size`
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
- created_utc: `2026-06-30T01:34:47.951767+00:00`

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

- episode_return: `-101.265323`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `22.650503`
- pi_loss_mean: `-0.675054`
- kl_mean: `535.218749`
- eta_mean: `2.905816`

### Train episode 2

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.064947`
- pi_loss_mean: `-0.694821`
- kl_mean: `0.000147`
- eta_mean: `2.919798`

### Train episode 3

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.185826`
- pi_loss_mean: `-0.694831`
- kl_mean: `0.000018`
- eta_mean: `2.919624`

### Train episode 4

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.163677`
- pi_loss_mean: `-0.694813`
- kl_mean: `0.000630`
- eta_mean: `2.919444`

### Train episode 5

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.302671`
- pi_loss_mean: `-0.694839`
- kl_mean: `0.005422`
- eta_mean: `2.919230`

### Train episode 6

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.012100`
- pi_loss_mean: `-0.694829`
- kl_mean: `0.000615`
- eta_mean: `2.918881`

### Train episode 7

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.174864`
- pi_loss_mean: `-0.694836`
- kl_mean: `0.021146`
- eta_mean: `2.918494`

### Train episode 8

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.609390`
- pi_loss_mean: `-0.694827`
- kl_mean: `0.004331`
- eta_mean: `2.917997`

### Train episode 9

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.101712`
- pi_loss_mean: `-0.694818`
- kl_mean: `0.021901`
- eta_mean: `2.917325`

### Train episode 10

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.025240`
- pi_loss_mean: `-0.694826`
- kl_mean: `-0.000001`
- eta_mean: `2.916513`

### Train episode 11

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.292492`
- pi_loss_mean: `-0.694832`
- kl_mean: `-0.000001`
- eta_mean: `2.915264`

### Train episode 12

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.143429`
- pi_loss_mean: `-0.694816`
- kl_mean: `0.020424`
- eta_mean: `2.913728`

### Train episode 13

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.035100`
- pi_loss_mean: `-0.694836`
- kl_mean: `-0.000001`
- eta_mean: `2.911957`

### Train episode 14

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.060438`
- pi_loss_mean: `-0.694836`
- kl_mean: `-0.000001`
- eta_mean: `2.909254`

### Train episode 15

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.467400`
- pi_loss_mean: `-0.694837`
- kl_mean: `-0.000001`
- eta_mean: `2.905761`

### Train episode 16

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.155659`
- pi_loss_mean: `-0.694817`
- kl_mean: `-0.000001`
- eta_mean: `2.901251`

### Train episode 17

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.045641`
- pi_loss_mean: `-0.694831`
- kl_mean: `-0.000001`
- eta_mean: `2.895433`

### Train episode 18

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.175661`
- pi_loss_mean: `-0.694821`
- kl_mean: `-0.000001`
- eta_mean: `2.887937`

### Train episode 19

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.057062`
- pi_loss_mean: `-0.694825`
- kl_mean: `-0.000001`
- eta_mean: `2.878291`

### Train episode 20

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.071048`
- pi_loss_mean: `-0.694827`
- kl_mean: `-0.000001`
- eta_mean: `2.865898`

### Train episode 21

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.306659`
- pi_loss_mean: `-0.694834`
- kl_mean: `-0.000001`
- eta_mean: `2.850015`

### Train episode 22

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.081311`
- pi_loss_mean: `-0.694813`
- kl_mean: `24.369070`
- eta_mean: `2.922364`

### Train episode 23

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.067972`
- pi_loss_mean: `-0.694834`
- kl_mean: `-0.000001`
- eta_mean: `3.158462`

### Train episode 24

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.068864`
- pi_loss_mean: `-0.694823`
- kl_mean: `-0.000001`
- eta_mean: `3.156363`

### Train episode 25

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.161160`
- pi_loss_mean: `-0.694841`
- kl_mean: `-0.000001`
- eta_mean: `3.153652`

### Train episode 26

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.087318`
- pi_loss_mean: `-0.694822`
- kl_mean: `-0.000001`
- eta_mean: `3.150149`

### Train episode 27

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.199815`
- pi_loss_mean: `-0.694835`
- kl_mean: `-0.000001`
- eta_mean: `3.145626`

### Train episode 28

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.266359`
- pi_loss_mean: `-0.694815`
- kl_mean: `-0.000001`
- eta_mean: `3.139791`

### Train episode 29

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.065973`
- pi_loss_mean: `-0.694822`
- kl_mean: `-0.000001`
- eta_mean: `3.132268`

### Train episode 30

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.289867`
- pi_loss_mean: `-0.694831`
- kl_mean: `-0.000001`
- eta_mean: `3.122585`

### Train episode 31

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.104543`
- pi_loss_mean: `-0.694834`
- kl_mean: `-0.000001`
- eta_mean: `3.110138`

### Train episode 32

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.067170`
- pi_loss_mean: `-0.694819`
- kl_mean: `-0.000001`
- eta_mean: `3.094173`

### Train episode 33

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.136251`
- pi_loss_mean: `-0.694803`
- kl_mean: `-0.000001`
- eta_mean: `3.073749`

### Train episode 34

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.074814`
- pi_loss_mean: `-0.694841`
- kl_mean: `-0.000001`
- eta_mean: `3.047710`

### Train episode 35

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.092712`
- pi_loss_mean: `-0.694816`
- kl_mean: `-0.000001`
- eta_mean: `3.014656`

### Train episode 36

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.141169`
- pi_loss_mean: `-0.694832`
- kl_mean: `-0.000001`
- eta_mean: `2.972925`

### Train episode 37

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.085289`
- pi_loss_mean: `-0.694828`
- kl_mean: `-0.000001`
- eta_mean: `2.920609`

### Train episode 38

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.075048`
- pi_loss_mean: `-0.694808`
- kl_mean: `-0.000001`
- eta_mean: `2.855592`

### Train episode 39

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.092697`
- pi_loss_mean: `-0.694846`
- kl_mean: `-0.000001`
- eta_mean: `2.775663`

### Train episode 40

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.137909`
- pi_loss_mean: `-0.694818`
- kl_mean: `-0.000001`
- eta_mean: `2.678717`

### Train episode 41

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.119136`
- pi_loss_mean: `-0.694846`
- kl_mean: `-0.000001`
- eta_mean: `2.563033`

### Train episode 42

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.090285`
- pi_loss_mean: `-0.694842`
- kl_mean: `-0.000001`
- eta_mean: `2.427662`

### Train episode 43

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.052143`
- pi_loss_mean: `-0.694860`
- kl_mean: `-0.000001`
- eta_mean: `2.272841`

### Train episode 44

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.081268`
- pi_loss_mean: `-0.694840`
- kl_mean: `-0.000001`
- eta_mean: `2.100365`

### Train episode 45

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.114087`
- pi_loss_mean: `-0.694829`
- kl_mean: `-0.000001`
- eta_mean: `1.913753`

### Train episode 46

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.142968`
- pi_loss_mean: `-0.694828`
- kl_mean: `-0.000001`
- eta_mean: `1.718109`

### Train episode 47

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.067020`
- pi_loss_mean: `-0.694843`
- kl_mean: `-0.000001`
- eta_mean: `1.519613`

### Train episode 48

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.050655`
- pi_loss_mean: `-0.694840`
- kl_mean: `-0.000001`
- eta_mean: `1.324731`

### Train episode 49

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.089516`
- pi_loss_mean: `-0.694832`
- kl_mean: `-0.000001`
- eta_mean: `1.139353`

### Train episode 50

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.073131`
- pi_loss_mean: `-0.694831`
- kl_mean: `-0.000001`
- eta_mean: `0.968108`

### Eval episode 1

- episode_return: `-51.600000`
- steps: `516`

### Eval episode 2

- episode_return: `-51.600000`
- steps: `516`

