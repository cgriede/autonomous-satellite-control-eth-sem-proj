"""1D camera observation line codes shared without importing environment_definition."""

import numpy as np

# Filled when camera optics were not run (e.g. kinematic-only trajectory helper).
OBSERVATION_LINE_NOT_COMPUTED = np.int8(-99)

# Default bin count; keep in sync with SIMULATION.camera_observation_line_n_bins.
DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS = 100
