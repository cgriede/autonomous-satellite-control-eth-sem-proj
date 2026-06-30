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
- created_utc: `2026-06-30T02:08:18.722494+00:00`

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

- episode_return: `-66.524118`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `17.197823`
- pi_loss_mean: `-0.862322`
- kl_mean: `916.248466`
- eta_mean: `2.793149`

### Train episode 2

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.596597`
- pi_loss_mean: `-0.869821`
- kl_mean: `-0.000001`
- eta_mean: `2.796055`

### Train episode 3

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.297889`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `2.796055`

### Train episode 4

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.172402`
- pi_loss_mean: `-0.869813`
- kl_mean: `-0.000001`
- eta_mean: `2.795990`

### Train episode 5

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `6.652577`
- pi_loss_mean: `-0.869839`
- kl_mean: `-0.000001`
- eta_mean: `2.795820`

### Train episode 6

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.691942`
- pi_loss_mean: `-0.869829`
- kl_mean: `-0.000001`
- eta_mean: `2.795648`

### Train episode 7

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.343199`
- pi_loss_mean: `-0.869836`
- kl_mean: `-0.000001`
- eta_mean: `2.795476`

### Train episode 8

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.165622`
- pi_loss_mean: `-0.869827`
- kl_mean: `-0.000001`
- eta_mean: `2.795221`

### Train episode 9

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.092951`
- pi_loss_mean: `-0.869818`
- kl_mean: `-0.000001`
- eta_mean: `2.794877`

### Train episode 10

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.695074`
- pi_loss_mean: `-0.869826`
- kl_mean: `-0.000001`
- eta_mean: `2.794441`

### Train episode 11

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `3.069231`
- pi_loss_mean: `-0.869832`
- kl_mean: `-0.000001`
- eta_mean: `2.793878`

### Train episode 12

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1.222034`
- pi_loss_mean: `-0.869816`
- kl_mean: `-0.000001`
- eta_mean: `2.793145`

### Train episode 13

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.124740`
- pi_loss_mean: `-0.869836`
- kl_mean: `-0.000001`
- eta_mean: `2.792196`

### Train episode 14

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.305574`
- pi_loss_mean: `-0.869835`
- kl_mean: `-0.000001`
- eta_mean: `2.790968`

### Train episode 15

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.076695`
- pi_loss_mean: `-0.869837`
- kl_mean: `-0.000001`
- eta_mean: `2.789381`

### Train episode 16

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.137407`
- pi_loss_mean: `-0.869817`
- kl_mean: `-0.000001`
- eta_mean: `2.787327`

### Train episode 17

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.131600`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `2.784674`

### Train episode 18

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.966438`
- pi_loss_mean: `-0.869821`
- kl_mean: `-0.000001`
- eta_mean: `2.781246`

### Train episode 19

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.362712`
- pi_loss_mean: `-0.869825`
- kl_mean: `-0.000001`
- eta_mean: `2.776822`

### Train episode 20

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.110005`
- pi_loss_mean: `-0.869827`
- kl_mean: `-0.000001`
- eta_mean: `2.771116`

### Train episode 21

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.160930`
- pi_loss_mean: `-0.869834`
- kl_mean: `-0.000001`
- eta_mean: `2.763763`

### Train episode 22

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.119956`
- pi_loss_mean: `-0.869813`
- kl_mean: `-0.000001`
- eta_mean: `2.754303`

### Train episode 23

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.190900`
- pi_loss_mean: `-0.869834`
- kl_mean: `-0.000001`
- eta_mean: `2.742152`

### Train episode 24

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.400422`
- pi_loss_mean: `-0.869823`
- kl_mean: `-0.000001`
- eta_mean: `2.726583`

### Train episode 25

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.092946`
- pi_loss_mean: `-0.869841`
- kl_mean: `-0.000001`
- eta_mean: `2.706692`

### Train episode 26

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.084635`
- pi_loss_mean: `-0.869822`
- kl_mean: `-0.000001`
- eta_mean: `2.681372`

### Train episode 27

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.174285`
- pi_loss_mean: `-0.869835`
- kl_mean: `-0.000001`
- eta_mean: `2.649295`

### Train episode 28

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.679285`
- pi_loss_mean: `-0.869815`
- kl_mean: `-0.000001`
- eta_mean: `2.608905`

### Train episode 29

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.109978`
- pi_loss_mean: `-0.869822`
- kl_mean: `-0.000001`
- eta_mean: `2.558433`

### Train episode 30

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.124537`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `2.495963`

### Train episode 31

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.408615`
- pi_loss_mean: `-0.869834`
- kl_mean: `-0.000001`
- eta_mean: `2.419553`

### Train episode 32

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.098168`
- pi_loss_mean: `-0.869819`
- kl_mean: `-0.000001`
- eta_mean: `2.327444`

### Train episode 33

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.072443`
- pi_loss_mean: `-0.869803`
- kl_mean: `-0.000001`
- eta_mean: `2.218344`

### Train episode 34

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.073830`
- pi_loss_mean: `-0.869841`
- kl_mean: `-0.000001`
- eta_mean: `2.091790`

### Train episode 35

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.103358`
- pi_loss_mean: `-0.869816`
- kl_mean: `-0.000001`
- eta_mean: `1.948512`

### Train episode 36

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.200153`
- pi_loss_mean: `-0.869832`
- kl_mean: `-0.000001`
- eta_mean: `1.790698`

### Train episode 37

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.077596`
- pi_loss_mean: `-0.869828`
- kl_mean: `-0.000001`
- eta_mean: `1.622052`

### Train episode 38

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.105382`
- pi_loss_mean: `-0.869808`
- kl_mean: `-0.000001`
- eta_mean: `1.447533`

### Train episode 39

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.119960`
- pi_loss_mean: `-0.869846`
- kl_mean: `-0.000001`
- eta_mean: `1.272792`

### Train episode 40

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.103355`
- pi_loss_mean: `-0.869818`
- kl_mean: `-0.000001`
- eta_mean: `1.103427`

### Train episode 41

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.130916`
- pi_loss_mean: `-0.869846`
- kl_mean: `-0.000001`
- eta_mean: `0.944253`

### Train episode 42

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.067379`
- pi_loss_mean: `-0.869842`
- kl_mean: `-0.000001`
- eta_mean: `0.798803`

### Train episode 43

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.063808`
- pi_loss_mean: `-0.869860`
- kl_mean: `-0.000001`
- eta_mean: `0.669141`

### Train episode 44

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.046651`
- pi_loss_mean: `-0.869840`
- kl_mean: `-0.000001`
- eta_mean: `0.555961`

### Train episode 45

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.206663`
- pi_loss_mean: `-0.869829`
- kl_mean: `-0.000001`
- eta_mean: `0.458873`

### Train episode 46

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.998857`
- pi_loss_mean: `-0.869828`
- kl_mean: `-0.000001`
- eta_mean: `0.376753`

### Train episode 47

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.086610`
- pi_loss_mean: `-0.869843`
- kl_mean: `-0.000001`
- eta_mean: `0.308061`

### Train episode 48

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.039950`
- pi_loss_mean: `-0.869840`
- kl_mean: `-0.000001`
- eta_mean: `0.251098`

### Train episode 49

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.077776`
- pi_loss_mean: `-0.869832`
- kl_mean: `-0.000001`
- eta_mean: `0.204175`

### Train episode 50

- episode_return: `-51.600000`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `0.090905`
- pi_loss_mean: `-0.869831`
- kl_mean: `-0.000001`
- eta_mean: `0.165718`

### Eval episode 1

- episode_return: `-51.600000`
- steps: `516`

### Eval episode 2

- episode_return: `-51.600000`
- steps: `516`

