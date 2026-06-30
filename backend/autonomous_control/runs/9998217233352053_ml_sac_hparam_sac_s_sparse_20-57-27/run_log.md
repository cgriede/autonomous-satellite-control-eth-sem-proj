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
- created_utc: `2026-06-29T20:57:27.947687+00:00`

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

- episode_return: `-75.363632`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `54.662676`
- pi_loss_mean: `-10.144296`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-10.341123`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `173.664890`
- pi_loss_mean: `-25.607606`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-36.620379`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `352.305334`
- pi_loss_mean: `-39.396358`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-9.041974`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `434.886421`
- pi_loss_mean: `-49.026374`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `36.155882`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `593.375848`
- pi_loss_mean: `-56.697983`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-69.494744`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `629.337269`
- pi_loss_mean: `-61.028448`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-41.000578`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `770.756563`
- pi_loss_mean: `-65.630104`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-41.309388`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2007.453497`
- pi_loss_mean: `-80.896886`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-40.731342`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2147.430456`
- pi_loss_mean: `-110.906143`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-42.518505`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2152.423225`
- pi_loss_mean: `-128.403453`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-39.932147`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1998.471835`
- pi_loss_mean: `-139.531903`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-37.404426`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1684.837681`
- pi_loss_mean: `-147.175702`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-40.693320`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1848.884721`
- pi_loss_mean: `-152.664670`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-37.416709`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `2189.608139`
- pi_loss_mean: `-156.236648`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-40.318301`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1760.151148`
- pi_loss_mean: `-156.293147`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-35.930870`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1643.335696`
- pi_loss_mean: `-153.669551`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `-39.149904`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1334.127521`
- pi_loss_mean: `-149.735242`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-71.911285`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1161.551295`
- pi_loss_mean: `-141.243546`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-72.322526`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1159.409375`
- pi_loss_mean: `-125.470180`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-74.478701`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `956.217154`
- pi_loss_mean: `-111.262331`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-30.537484`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `978.384516`
- pi_loss_mean: `-105.360035`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-33.666638`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `862.261726`
- pi_loss_mean: `-100.464618`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-72.638576`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1344.556754`
- pi_loss_mean: `-96.104467`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-76.009811`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `987.301599`
- pi_loss_mean: `-91.592186`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-78.220769`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1091.113455`
- pi_loss_mean: `-84.750572`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-74.957359`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `737.753937`
- pi_loss_mean: `-79.101016`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-76.771493`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `641.413252`
- pi_loss_mean: `-73.737886`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-76.557752`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `778.002863`
- pi_loss_mean: `-66.278595`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-76.322308`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `529.024421`
- pi_loss_mean: `-61.454792`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `18.714587`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `589.848781`
- pi_loss_mean: `-55.831107`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `9.181907`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `582.873727`
- pi_loss_mean: `-48.740020`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `9.914157`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `397.017712`
- pi_loss_mean: `-43.921590`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-16.458181`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `374.435338`
- pi_loss_mean: `-39.557042`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-19.623429`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `382.498886`
- pi_loss_mean: `-35.609417`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-34.885746`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `385.935017`
- pi_loss_mean: `-33.541257`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-11.687946`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `399.344234`
- pi_loss_mean: `-32.371654`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-53.661399`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `351.459103`
- pi_loss_mean: `-31.280894`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 38

- episode_return: `44.215232`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `349.845026`
- pi_loss_mean: `-30.818937`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 39

- episode_return: `-7.725991`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `305.744135`
- pi_loss_mean: `-30.353441`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 40

- episode_return: `87.894141`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `281.901067`
- pi_loss_mean: `-30.221582`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 41

- episode_return: `27.100999`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `237.849645`
- pi_loss_mean: `-29.142369`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 42

- episode_return: `0.434438`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `272.236728`
- pi_loss_mean: `-30.521691`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 43

- episode_return: `53.001771`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `292.413173`
- pi_loss_mean: `-30.903401`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 44

- episode_return: `15.557884`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `265.364963`
- pi_loss_mean: `-32.787741`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 45

- episode_return: `-39.227493`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `259.182165`
- pi_loss_mean: `-34.638642`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 46

- episode_return: `34.696512`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `241.926180`
- pi_loss_mean: `-35.002950`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 47

- episode_return: `29.714303`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `243.817601`
- pi_loss_mean: `-35.152860`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 48

- episode_return: `88.787950`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `235.928510`
- pi_loss_mean: `-35.798158`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 49

- episode_return: `-31.027570`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `278.830603`
- pi_loss_mean: `-36.084404`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 50

- episode_return: `7.000595`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `289.437607`
- pi_loss_mean: `-36.470313`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `69.838417`
- steps: `516`

### Eval episode 2

- episode_return: `69.838417`
- steps: `516`

