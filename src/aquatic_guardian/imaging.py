"""Underwater image formation (Akkaynak & Treibitz 2018, 2019).

I_c = J_c exp(-beta_D z) + B_inf (1 - exp(-beta_B z))
with DIFFERENT attenuation coefficients for the direct signal (beta_D) and
backscatter (beta_B). Using one coefficient (the atmospheric-haze model) is a
common error. Inversion divides by transmittance t = exp(-beta_D z), so noise
is amplified by 1/t. Frames with t < t_min are flagged as not recoverable and
should lower detection probability p in the occupancy model rather than be
silently scored as absences.
"""
from __future__ import annotations
import numpy as np

T_MIN_DEFAULT = 0.1


def forward(J, z, beta_d, beta_b, b_inf):
    t = np.exp(-beta_d * z)
    return J * t + b_inf * (1 - np.exp(-beta_b * z))


def invert(I, z, beta_d, beta_b, b_inf, t_min: float = T_MIN_DEFAULT) -> dict:
    t = np.exp(-beta_d * np.asarray(z, float))
    backscatter = b_inf * (1 - np.exp(-beta_b * np.asarray(z, float)))
    recoverable = t >= t_min
    J = (np.asarray(I, float) - backscatter) / np.maximum(t, t_min)
    return {"J": J, "transmittance": t, "noise_gain": 1.0 / np.maximum(t, 1e-300),
            "recoverable": recoverable}
