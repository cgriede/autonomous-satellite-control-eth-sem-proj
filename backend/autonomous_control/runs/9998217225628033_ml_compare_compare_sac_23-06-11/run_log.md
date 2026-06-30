# S01 notebook 08 — MPO training

## Metadata

- seed: `7`
- experiment_name: `compare compare sac`
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
- created_utc: `2026-06-29T23:06:11.967100+00:00`

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

- episode_return: `-72.108360`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `60.927609`
- pi_loss_mean: `-10.983669`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 2

- episode_return: `-75.941070`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `130.419532`
- pi_loss_mean: `-32.503682`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 3

- episode_return: `-76.636788`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `450.796104`
- pi_loss_mean: `-51.611391`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 4

- episode_return: `-78.074452`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `794.538176`
- pi_loss_mean: `-68.643768`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 5

- episode_return: `-80.439785`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1167.798949`
- pi_loss_mean: `-83.131479`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 6

- episode_return: `-82.130258`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1414.942407`
- pi_loss_mean: `-94.127549`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 7

- episode_return: `-84.552189`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1528.764375`
- pi_loss_mean: `-101.035973`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 8

- episode_return: `-84.013550`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1497.201066`
- pi_loss_mean: `-103.452017`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 9

- episode_return: `-79.851785`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1335.368487`
- pi_loss_mean: `-105.170486`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 10

- episode_return: `-75.894199`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `1126.097599`
- pi_loss_mean: `-104.057938`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 11

- episode_return: `-75.724431`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `979.312980`
- pi_loss_mean: `-100.556620`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 12

- episode_return: `-71.324187`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `821.763453`
- pi_loss_mean: `-94.838840`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 13

- episode_return: `-74.669067`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `711.772191`
- pi_loss_mean: `-90.062929`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 14

- episode_return: `-75.465502`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `629.146575`
- pi_loss_mean: `-87.493861`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 15

- episode_return: `-66.909278`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `538.178166`
- pi_loss_mean: `-84.248125`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 16

- episode_return: `-32.002791`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `569.741381`
- pi_loss_mean: `-86.830074`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 17

- episode_return: `5.332035`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `562.754823`
- pi_loss_mean: `-91.878968`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 18

- episode_return: `-71.101221`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `631.018930`
- pi_loss_mean: `-98.858986`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 19

- episode_return: `-63.752038`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `687.553066`
- pi_loss_mean: `-110.889440`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 20

- episode_return: `-27.000222`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `620.613620`
- pi_loss_mean: `-117.492424`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 21

- episode_return: `-38.186162`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `617.688888`
- pi_loss_mean: `-126.251615`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 22

- episode_return: `-26.131478`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `627.954972`
- pi_loss_mean: `-130.763470`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 23

- episode_return: `-36.187137`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `568.305143`
- pi_loss_mean: `-132.805586`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 24

- episode_return: `-37.623870`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `517.432065`
- pi_loss_mean: `-131.083028`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 25

- episode_return: `-47.125637`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `522.067471`
- pi_loss_mean: `-132.827838`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 26

- episode_return: `-18.754834`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `482.683873`
- pi_loss_mean: `-129.727906`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 27

- episode_return: `-22.980067`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `474.696674`
- pi_loss_mean: `-127.599497`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 28

- episode_return: `-41.212163`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `455.974400`
- pi_loss_mean: `-125.644935`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 29

- episode_return: `-24.271165`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `471.622756`
- pi_loss_mean: `-122.745182`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 30

- episode_return: `-27.869811`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `451.383722`
- pi_loss_mean: `-120.275450`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 31

- episode_return: `-56.152192`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `448.037623`
- pi_loss_mean: `-117.420850`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 32

- episode_return: `-14.381118`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `463.758908`
- pi_loss_mean: `-115.675774`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 33

- episode_return: `-55.242641`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `461.037688`
- pi_loss_mean: `-112.638278`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 34

- episode_return: `-28.759713`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `539.973184`
- pi_loss_mean: `-109.315911`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 35

- episode_return: `-22.741391`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `460.202733`
- pi_loss_mean: `-106.038636`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 36

- episode_return: `-10.471573`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `428.134887`
- pi_loss_mean: `-102.134553`
- kl_mean: `nan`
- eta_mean: `nan`

### Train episode 37

- episode_return: `-44.822155`
- steps: `516`
- n_train_updates: `516`
- q_loss_mean: `397.022252`
- pi_loss_mean: `-98.048609`
- kl_mean: `nan`
- eta_mean: `nan`

### Eval episode 1

- episode_return: `-10.805769`
- steps: `516`

### Eval episode 2

- episode_return: `-33.533768`
- steps: `516`

