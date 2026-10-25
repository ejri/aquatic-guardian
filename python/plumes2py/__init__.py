"""plumes2py: a Python rebuild of EPA PLUMES2.0 (UM3 near field + Brooks far
field) with the extended thermal, biological and regulatory metrics used by
Aquatic Guardian. See VALIDATION.md for how it reproduces the EPA reference."""
__version__ = "1.0.0"

from .inputs import (Ambient, AmbientRow, Diffuser, Effluent, MixingZone, Scenario,  # noqa: E402,F401
                     Settings, load_plumes2_csvs, reference_example)
from .um3 import run_nearfield  # noqa: E402,F401
from .brooks import run_farfield  # noqa: E402,F401
from .model import run  # noqa: E402,F401
