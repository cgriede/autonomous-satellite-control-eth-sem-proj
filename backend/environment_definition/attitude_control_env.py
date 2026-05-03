import gymnasium as gym
import numpy as np
from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward
from environment_definition.constants.SIMULATION import SIMULATION

from .constants.SATELLITE import *
from simulation import AttitudeState2D, propagate_reaction_wheel_attitude_2d
from simulation.camera_2d import calculate_fov_angles
from simulation.reaction_wheel import ReactionWheel


class SatelliteAttitudeControlEnv(gym.Env):
    """Gym environment for single-axis satellite attitude control episodes."""

    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, render_mode=None, reward_config: RewardConfig | None = None):
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
        self.dt = 0.1 * ureg.s  # Time step (s)
        self.max_episode_steps = int(SIMULATION.max_episode_steps)

        # Canonical reward config (flags selected from MPOConfig.reward when
        # supplied by training runtime; default = all components on).
        self.reward_config = reward_config if reward_config is not None else RewardConfig()

        # Cache altitude and half-FOV for reward-signal derivation.
        self._altitude_km = CAMERA_ALTITUDE.to(ureg.km).magnitude
        _, vfov_q = calculate_fov_angles()
        self._half_vertical_fov_rad = 0.5 * float(vfov_q.to(ureg.rad).magnitude)

        # Observation:
        # [angle_rel_nadir, angular_velocity, angular_acceleration, angle_to_target, wheel_speed]
        high = np.array([np.pi, 5.0, 5.0, np.pi, self.omega_w_max * 1.1], dtype=np.float32)
        self.observation_space = gym.spaces.Box(-high, high, dtype=np.float32)

        # Action: torque on wheel
        tau_max_nm = self.tau_max.to(ureg.N * ureg.m).magnitude
        self.action_space = gym.spaces.Box(-tau_max_nm, tau_max_nm, shape=(1,), dtype=np.float32)

        self.render_mode = render_mode
        self.current_step = 0
        self.state = None
        self.target_theta = 0.0
        self._alpha_sat = 0.0
        self._theta = 0.0
        self._omega_s = 0.0
        self._omega_w = 0.0

    @staticmethod
    def _wrap_to_pi(angle_rad: float) -> float:
        return float(np.arctan2(np.sin(angle_rad), np.cos(angle_rad)))

    def _build_observation(self) -> np.ndarray:
        angle_rel_nadir = self._wrap_to_pi(self._theta)
        angle_to_target = self._wrap_to_pi(self._theta - self.target_theta)
        return np.array(
            [angle_rel_nadir, self._omega_s, self._alpha_sat, angle_to_target, self._omega_w],
            dtype=np.float32,
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._theta = float(np.random.uniform(-np.pi / 4, np.pi / 4))
        self._omega_s = float(np.random.uniform(-0.5, 0.5))
        self._omega_w = 0.0
        self._alpha_sat = 0.0
        self.target_theta = float(np.random.uniform(-np.pi / 3, np.pi / 3))
        self.state = self._build_observation()
        self.current_step = 0
        return self.state, {}

    def step(self, action):
        tau_max_nm = self.tau_max.to(ureg.N * ureg.m).magnitude
        tau = np.clip(action[0], -tau_max_nm, tau_max_nm)

        state = AttitudeState2D(
            theta=float(self._theta) * ureg.rad,
            omega_sat=float(self._omega_s) * ureg.rad / ureg.s,
            omega_wheel=float(self._omega_w) * ureg.rad / ureg.s,
        )
        tau_cmd = float(tau) * ureg.N * ureg.m
        tau_applied = self.reaction_wheel.compute_applied_torque(
            state=state, tau_cmd=tau_cmd
        )

        omega_w_before_q = state.omega_wheel

        next_state = propagate_reaction_wheel_attitude_2d(
            state=state,
            wheel_torque=tau_applied,
            sat_inertia=self.I_s,
            wheel_inertia=self.I_w,
            dt=self.dt,
        )
        theta = float(next_state.theta.to(ureg.rad).magnitude)
        omega_s = float(next_state.omega_sat.to(ureg.rad / ureg.s).magnitude)
        omega_w = float(next_state.omega_wheel.to(ureg.rad / ureg.s).magnitude)
        dt_s = float(self.dt.to(ureg.s).magnitude)
        self._alpha_sat = (omega_s - self._omega_s) / dt_s
        self._theta = theta
        self._omega_s = omega_s
        self._omega_w = omega_w
        self.state = self._build_observation()

        # Reward via the shared combiner entrypoint. In this control env
        # there is no full orbit geometry, so distance_to_target is a slant-range
        # proxy (altitude / cos(pointing_error)) and target_visible is derived
        # from whether the pointing error falls inside the vertical FOV.
        pointing_error_rad = float(np.abs(self._wrap_to_pi(theta - self.target_theta)))
        cos_err = float(np.cos(pointing_error_rad))
        if cos_err > 1e-3:
            d_to_target_km = self._altitude_km / cos_err
        else:
            # Effectively no line-of-sight to ground; beyond outer gate.
            d_to_target_km = 1.0e9
        target_visible = bool(pointing_error_rad < self._half_vertical_fov_rad)

        signals = RewardSignals(
            distance_to_target=d_to_target_km * ureg.km,
            picture_taken=True,
            target_visible=target_visible,
            wheel_inertia=self.I_w,
            omega_before=omega_w_before_q,
            omega_after=next_state.omega_wheel,
        )
        reward_total, reward_components = compute_reward(
            signals=signals, cfg=self.reward_config
        )
        reward = float(reward_total)

        self.current_step += 1
        terminated = np.abs(omega_w) > self.omega_w_max  # saturation fail
        truncated = self.current_step >= self.max_episode_steps

        info = {"reward_components": reward_components}
        return self.state, reward, terminated, truncated, info

    def render(self):
        if self.render_mode == "human":
            print(
                f"Step {self.current_step} | θ={self._theta:.3f} rad | "
                f"ω_s={self._omega_s:.3f} rad/s | α_s={self._alpha_sat:.3f} rad/s² | "
                f"Δθ_target={self._wrap_to_pi(self._theta - self.target_theta):.3f} rad | "
                f"ω_w={self._omega_w:.3f} rad/s"
            )
