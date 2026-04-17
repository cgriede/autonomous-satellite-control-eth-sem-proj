"""1D camera observation line codes shared without importing environment_definition."""

import numpy as np

# Filled when camera optics were not run (e.g. kinematic-only trajectory helper).
OBSERVATION_LINE_NOT_COMPUTED = np.int8(-99)

# Default bin count; keep in sync with SIMULATION.camera_observation_line_n_bins.
DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS = 100

# Shared observation codes used by camera and fixed-ground line classifications.
OBSERVATION_SPACE = np.int8(0)
OBSERVATION_EARTH = np.int8(1)
OBSERVATION_CLOUD = np.int8(2)
OBSERVATION_TARGET = np.int8(3)

# Fixed-ground only code: mark the bin corresponding to boresight cone hit on Earth.
FIXED_GROUND_CONE_HIT_EARTH = np.int8(4)
