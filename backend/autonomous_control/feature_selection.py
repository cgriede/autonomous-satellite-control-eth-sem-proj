from dataclasses import dataclass

@dataclass(frozen=True)
class AutonomousControllerState:
    #satellite position
    #target position (as requested by mission objective)
    #satellite orientation / attitude
    #camera view preclassified as space, earth, cloud, target

@dataclass(frozen=True)
class AutonomousControllerAction:
    #torque on reaction wheel
    #send image of target to command center (target is visible)