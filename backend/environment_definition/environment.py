import gymnasium as gym
import numpy as np
from .constants.SATELLITE import *
from simulation import AttitudeState2D, propagate_reaction_wheel_attitude_2d

class SatelliteAttitude2D(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, render_mode=None):
        self.I_s = MOMENT_OF_INERTIA_2D.to(ureg.kg * ureg.m**2)
        self.I_w = (REACTION_WHEEL_MAX_MOMENTUM / REACTION_WHEEL_MAX_TORQUE).to(ureg.kg * ureg.m**2)
        self.tau_max = (0.02 * ureg.N * ureg.m).to(ureg.N * ureg.m)
        self.omega_w_max = 150.0 # Wheel saturation speed (rad/s)
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

        next_state = propagate_reaction_wheel_attitude_2d(
            state=AttitudeState2D(
                theta=float(theta) * ureg.rad,
                omega_sat=float(omega_s) * ureg.rad / ureg.s,
                omega_wheel=float(omega_w) * ureg.rad / ureg.s,
            ),
            wheel_torque=float(tau) * ureg.N * ureg.m,
            sat_inertia=self.I_s,
            wheel_inertia=self.I_w,
            dt=self.dt,
        )
        theta = next_state.theta.to(ureg.rad).magnitude
        omega_s = next_state.omega_sat.to(ureg.rad / ureg.s).magnitude
        omega_w = next_state.omega_wheel.to(ureg.rad / ureg.s).magnitude

        self.state = np.array([theta, omega_s, omega_w])

        # Reward: pointing accuracy + low energy + avoid saturation
        pointing_error = np.abs(theta - self.target_theta)
        reward = -pointing_error**2 - 0.05 * omega_w**2 - 0.01 * tau**2
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