# ML training documentation

## V1
first we try and train a very simple controller which makes a pointing manouver directly at the target, no exploration just simple control

### reward
the reward is per timestep / frame as a sum over timesteps
0 when the fov cone is aligned with the target
-1 when the fov cone is not aligned with the target

### simplifications
clouds have no effect yet (no view blocker)
camera observation is fed to the agent directly as 1d camera array (earth, target, space) (no cloud for now)

### goals
understanding the minimum complexity of the agent to do this very simple control task
random orientation initialization (not overfitting to a specific pattern, should learn to stabilize)
random spin initialization

## V2
in this second iteration we get closer to the real objective