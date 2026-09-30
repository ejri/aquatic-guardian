"""Aquatic Guardian: verified screening physics, ecology and disclosure tools for
the aquatic, ecological and animal-sentience impacts of data centres.

Every function is a *screening* calculation. None replaces a regulatory
mixing-zone study, a CWA §316(a)/(b) demonstration, a Fisheries Act
authorisation, or species-expert review. See docs/VERIFICATION.md for the
validation status of each module.
"""
__version__ = "0.2.1"

from . import (cooling, intake, plume, tidal, numerics, seawater, water_quality,
               criteria, sentience, occupancy, imaging, tracking, bioenergetics,
               disclosure, handoff, screening)

__all__ = ["cooling", "intake", "plume", "tidal", "numerics", "seawater",
           "water_quality", "criteria", "sentience", "occupancy", "imaging",
           "tracking", "bioenergetics", "disclosure", "handoff", "screening"]
