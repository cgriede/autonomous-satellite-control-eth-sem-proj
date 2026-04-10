# 11.11.1111 TEMPLATE ##########################################################################################
# Open questions blocking progress
# Quantities estimations, simplifications
# don't know if these matter
# Input/Output Data of sensors / control systems
# Ideas / Brainstorming







# 27.03.2025 W2 ##########################################################################################
# Open questions blocking progress
-mission objective?
-Framerate camera

# Quantities estimations, simplifications
-if possible and weather good let initiation of a maneuver start earlier, use less angular momentum
-found matching datasheet of reaction wheel from rocket lab, is this the right one? -datasheet star tracker, camera etc datasheet? (I can search docs myself lol, less friction)
-current other build documents?


# don't know if these matter

-assumptions for camera movement speed / fps

# Control Agent:
## Reward function outline:
reward:
-get pointing to ground connection, 10 images gives full reward, reward size dependant on closeness to the objective, different angles (10images taken in 1s are worth less than 10 images taken in a full overflight)
overflight meaning when the observer fully is in the horizon until is fully in the horizon again (no connection possible otherwise due to earth obstruction, but we can already prep for the next manouver given the current cloud state and mission adjustment)

deduction:
-energy used
-pictures outside visible area (too far in the horizon, or cloudy images)
# Ideas / Brainstorming
If it does not work because camera has no chance at scanning the sky this fast (since the picture/second is too small):
pivot into satellite control for energy efficiency on mission objective









# 20.03.2025 W1 ##########################################################################################

# Open questions blocking progress
Dissuss these questions with Alex in Meetings or directly via Mial / Teams.


# Quantities estimations, simplifications
AOCS
- max angular acceleration  [rad/s^{2}] RW
- max angular regen deceleration RW
- MoI for 2d Case, 1 axis rotation
- MoI Matrix

- orbit height / flight level (upper lower bound)
- 

## minimal sensor inclination (to earth)
at how many degrees is the camera able to see the target?

## max viewing distance for useful observer resolution
what must the pixel density be in order for a target to be observed?

# don't know if these matter
- orientation signal delay?

# Input/Output Data of sensors / control systems
- how do we represent the location of the satellite, what coord system?
- (presume to be given by flight tracker)
- what shape / coordinate system is the target vector for the AOCS in?