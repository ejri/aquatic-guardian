"""Single-season occupancy with imperfect detection (MacKenzie et al. 2002).

Turbidity belongs in the DETECTION sub-model (logit p_ij = a0 + a1 * turb_ij)
unless there is independent evidence that habitat use changes. Omitting it
lets turbidity-driven detection failure masquerade as an ecological effect:
see tests/test_occupancy.py, which reproduces that confound.
Requires >= 2 (ideally >= 3) repeat surveys per site under closure.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


def _design(n_sites: int, x) -> np.ndarray:
    if x is None:
        return np.ones((n_sites, 1))
    x = np.atleast_2d(np.asarray(x, float))
    if x.shape[0] != n_sites:
        x = x.T
    return np.column_stack([np.ones(n_sites), x])


def neg_log_lik(theta: np.ndarray, y: np.ndarray, x_psi: np.ndarray, w_p: np.ndarray) -> float:
    """y: sites x surveys (0/1, NaN = not surveyed). w_p: sites x surveys x k detection covariates (incl. intercept)."""
    k_psi = x_psi.shape[1]
    psi = expit(x_psi @ theta[:k_psi])
    p = expit(np.einsum("ijk,k->ij", w_p, theta[k_psi:]))
    obs = ~np.isnan(y)
    yy = np.where(obs, y, 0.0)
    pp = np.clip(p, 1e-12, 1 - 1e-12)
    log_det = np.where(obs, yy * np.log(pp) + (1 - yy) * np.log(1 - pp), 0.0).sum(axis=1)
    detected = (np.nan_to_num(y) > 0).any(axis=1)
    lik = np.where(detected, psi * np.exp(log_det), psi * np.exp(log_det) + (1 - psi))
    return -np.log(np.clip(lik, 1e-300, None)).sum()


def fit(y, psi_covariates=None, detection_covariates=None) -> dict:
    y = np.asarray(y, float)
    n, j = y.shape
    x_psi = _design(n, psi_covariates)
    if detection_covariates is None:
        w_p = np.ones((n, j, 1))
    else:
        d = np.asarray(detection_covariates, float)
        d = d[..., None] if d.ndim == 2 else d
        w_p = np.concatenate([np.ones((n, j, 1)), d], axis=2)
    theta0 = np.zeros(x_psi.shape[1] + w_p.shape[2])
    res = minimize(neg_log_lik, theta0, args=(y, x_psi, w_p), method="BFGS")
    k = x_psi.shape[1]
    se = _standard_errors(res.x, y, x_psi, w_p)
    return {"theta": res.x, "se": se, "beta_psi": res.x[:k], "alpha_p": res.x[k:],
            "psi_hat": expit(x_psi @ res.x[:k]), "nll": res.fun, "converged": bool(res.success),
            "naive_occupancy": float((np.nan_to_num(y) > 0).any(axis=1).mean())}


def _standard_errors(theta, y, x_psi, w_p, h=1e-4) -> np.ndarray:
    """Wald standard errors from a central-difference Hessian of the NLL."""
    n = len(theta)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            e_i = np.eye(n)[i] * h
            e_j = np.eye(n)[j] * h
            f = lambda d: neg_log_lik(theta + d, y, x_psi, w_p)
            H[i, j] = H[j, i] = (f(e_i + e_j) - f(e_i - e_j) - f(-e_i + e_j) + f(-e_i - e_j)) / (4 * h * h)
    try:
        return np.sqrt(np.clip(np.diag(np.linalg.inv(H)), 0, None))
    except np.linalg.LinAlgError:
        return np.full(n, np.nan)
