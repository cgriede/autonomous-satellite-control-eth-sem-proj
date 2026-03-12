from dataclasses import dataclass


@dataclass(frozen=True)
class Satellite:
    mass: object
    star_tracker_max_maneuver_rate: object
    moment_of_inertia_2d: object
    reaction_wheel_max_torque: object
    reaction_wheel_max_momentum: object


@dataclass(frozen=True)
class Mission:
    altitude_lower_bound: object
    altitude_upper_bound: object
    sampled_altitude: object
    orbit_speed: object


@dataclass(frozen=True)
class Environment:
    earth_radius: object
    earth_gravitational_parameter: object
    simulation: object
    render: object
