import gymnasium as gym
import numpy as np
from .constants.SATELLITE import *
from simulation import AttitudeState2D, propagate_reaction_wheel_attitude_2d
from simulation.reaction_wheel import ReactionWheel

class SatelliteAttitude2D(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, render_mode=None):
        self.I_s = MOMENT_OF_INERTIA_2D.to(ureg.kg * ureg.m**2)
        self.tau_max = (0.02 * ureg.N * ureg.m).to(ureg.N * ureg.m)
        # Wheel saturation speed used for comparisons/reward termination.
        self.omega_w_max = 150.0  # rad/s (float, used against omega_w magnitudes)
        omega_w_max_q = self.omega_w_max * ureg.rad / ureg.s
        # Wheel inertia from max momentum and max wheel speed:
        # H_max [kg*m^2/s] = I_w [kg*m^2] * omega_w_max [1/s]
        self.I_w = (REACTION_WHEEL_MAX_MOMENTUM / omega_w_max_q).to(ureg.kg * ureg.m**2)
        self.reaction_wheel = ReactionWheel(
            wheel_inertia=self.I_w,
            # Safety cutoff threshold comes from the mission configuration.
            max_manouver_rate=STAR_TRACKER_MAX_MANEUVER_RATE,
        )
        self.dt = 0.1 * ureg.s   # Time step (s)
        self.max_episode_steps = 500

        # State: [theta (rad), omega_s (rad/s), omega_w (rad/s)]
        high = np.array([np.pi, 5.0, self.omega_w_max * 1.1], dtype=np.float32)
        self.observation_space = gym.spaces.Box(-high, high, dtype=np.float32)

        # Action: torque on wheel
        tau_max_nm = self.tau_max.to(ureg.N * ureg.m).magnitude
        self.action_space = gym.spaces.Box(-tau_max_nm, tau_max_nm, shape=(1,), dtype=np.float32)

        self.render_mode = render_mode
        self.current_step = 0
        self.state = None
        self.target_theta = 0.0  # Can randomize per reset

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.array([
            np.random.uniform(-np.pi/4, np.pi/4),  # initial angle error
            np.random.uniform(-0.5, 0.5),           # initial angular rate
            0.0                                      # wheel at rest
        ], dtype=np.float32)
        self.current_step = 0
        return self.state, {}

    def step(self, action):
        tau_max_nm = self.tau_max.to(ureg.N * ureg.m).magnitude
        tau = np.clip(action[0], -tau_max_nm, tau_max_nm)

        theta, omega_s, omega_w = self.state

        state = AttitudeState2D(
            theta=float(theta) * ureg.rad,
            omega_sat=float(omega_s) * ureg.rad / ureg.s,
            omega_wheel=float(omega_w) * ureg.rad / ureg.s,
        )
        tau_cmd = float(tau) * ureg.N * ureg.m
        tau_applied = self.reaction_wheel.compute_applied_torque(state=state, tau_cmd=tau_cmd)

        next_state = propagate_reaction_wheel_attitude_2d(
            state=state,
            wheel_torque=tau_applied,
            sat_inertia=self.I_s,
            wheel_inertia=self.I_w,
            dt=self.dt,
        )
        theta = next_state.theta.to(ureg.rad).magnitude
        omega_s = next_state.omega_sat.to(ureg.rad / ureg.s).magnitude
        omega_w = next_state.omega_wheel.to(ureg.rad / ureg.s).magnitude

        self.state = np.array([theta, omega_s, omega_w])

        # Reward: pointing accuracy + low energy + avoid saturation
        # In the 2D backend we keep the camera mapping 1D:
        # angular pointing error -> vertical sensor pixel offset via pinhole optics.
        #
        # Pixel coordinate (vertical, in-plane) for an off-boresight angle alpha:
        #   y = f * tan(alpha)
        #   pixel_offset_pixels = y / pixel_size
        pointing_error_rad = float(np.abs(theta - self.target_theta)) * ureg.rad
        focal_m = FOCAL_LENGTH.to(ureg.m).magnitude
        pixel_pitch_m = PIXEL_SIZE.to(ureg.m).magnitude
        pointing_error_mag_rad = pointing_error_rad.to(ureg.rad).magnitude
        pixel_offset_pixels = (focal_m * np.tan(pointing_error_mag_rad)) / pixel_pitch_m

        # Normalize to [0, 1] across the sensor half-height and clip for numerical stability.
        pixel_offset_norm = pixel_offset_pixels / (0.5 * float(N_PIXELS_Y))
        pixel_offset_norm_clipped = float(np.clip(pixel_offset_norm, 0.0, 1.0))

        tau_applied_nm = tau_applied.to(ureg.N * ureg.m).magnitude
        reward = -(pixel_offset_norm_clipped**2) - 0.05 * omega_w**2 - 0.01 * tau_applied_nm**2
        # Bonus for low wheel speed (proxy for energy/desat need)
        reward -= 0.1 * np.abs(omega_w) / self.omega_w_max

        self.current_step += 1
        terminated = np.abs(omega_w) > self.omega_w_max  # saturation fail
        truncated = self.current_step >= self.max_episode_steps

        return self.state, reward, terminated, truncated, {}

    # Simple text render; extend to matplotlib arrow for angle viz
    def render(self):
        if self.render_mode == "human":
            print(f"Step {self.current_step} | θ={self.state[0]:.3f} rad | ω_s={self.state[1]:.3f} | ω_w={self.state[2]:.3f}")