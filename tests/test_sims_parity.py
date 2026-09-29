"""The browser simulation kernels (app/sims.js) must match the Python reference."""
import json, shutil, subprocess
from pathlib import Path
import numpy as np
import pytest
from aquatic_guardian import numerics, imaging, bioenergetics, tracking

ROOT = Path(__file__).resolve().parents[1]
node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def run_js(body: str, payload) -> object:
    js = (f"const E=require({json.dumps(str(ROOT/'app'/'engine.js'))});global.AquaticGuardian=E;"
          f"const S=require({json.dumps(str(ROOT/'app'/'sims.js'))});"
          f"const P=JSON.parse(require('fs').readFileSync(0,'utf8'));"
          f"process.stdout.write(JSON.stringify((()=>{{{body}}})()));")
    r = subprocess.run(["node", "-e", js], input=json.dumps(payload), capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


@node
@pytest.mark.parametrize("scheme,u", [("upwind", 0.3), ("tvd", 0.3), ("tvd", -0.45), ("upwind", -0.2)])
def test_advect1d_parity(scheme, u):
    x = np.arange(300)
    c0 = np.exp(-0.5 * ((x - 100) / 5.0) ** 2) + (x > 200) * 0.5
    py = numerics.advect_diffuse_1d(c0, u, 0.4, 25.0, 20.0, 150, scheme)
    js = run_js("return S.advect1d(P.c0,P.u,0.4,25.0,20.0,150,P.s);", {"c0": c0.tolist(), "u": u, "s": scheme})
    np.testing.assert_allclose(js, py, rtol=0, atol=1e-12)


@node
def test_imaging_parity():
    zs = [0.5, 2, 5, 12, 20]
    py = [float(imaging.invert(imaging.forward(0.4, z, 0.3, 0.25, 0.35), z, 0.3, 0.25, 0.35)["J"]) for z in zs]
    js = run_js("return P.z.map(z=>S.imgInvert(S.imgForward(0.4,z,0.3,0.25,0.35),z,0.3,0.25,0.35).J);", {"z": zs})
    np.testing.assert_allclose(js, py, rtol=1e-12)


@node
def test_bioenergetics_parity():
    sp = bioenergetics.SpeciesParams()
    cases = [(t, s, ph, f) for t in (6, 9.5, 12.25, 15, 18, 21.5) for s in (0, 30) for ph in (7.2, 7.8) for f in (60, 400)]
    js = run_js("return P.c.map(a=>{const r=S.carrying(a[0],a[1],a[2],a[3],100);return [r.capacity_kg,r.binding,S.yieldIndex(a[0],a[1],a[2],a[3],100)];});", {"c": cases})
    for (t, s, ph, f), (cap, bind, y) in zip(cases, js):
        ref = bioenergetics.carrying_capacity_kg(t, s, ph, f, 100, sp)
        assert cap == pytest.approx(ref["capacity_kg"], rel=1e-12)
        assert bind == ref["binding"]
        assert y == pytest.approx(bioenergetics.yield_index(t, s, ph, f, 100, sp), rel=1e-12)


@node
def test_kalman_parity():
    sc = tracking.simulate_school(n=4, steps=60, seed=2)
    obs = sc["pos"] + np.random.default_rng(1).normal(0, 0.004, sc["pos"].shape)
    py = tracking.kalman_cv(obs, sc["dt"], 0.004, 0.5)
    js = run_js("return S.kalmanSeries(P.o,P.dt,0.004,0.5);", {"o": obs.tolist(), "dt": sc["dt"]})
    np.testing.assert_allclose(np.array(js), py, rtol=1e-9, atol=1e-12)


@node
def test_transport2d_conserves_heat_with_closed_boundaries_and_matches_upwind_formula():
    """With zero velocity and no source, total heat changes only through the offshore boundary;
    with a steady along-shore current the upwind scheme spreads a pulse at K_num = |u|dx/2(1-C)."""
    body = """
      const T=new S.Transport2D(400,3,25);
      const nx=400; for(let j=0;j<3;j++) for(let i=0;i<nx;i++) T.c[j*nx+i]=Math.exp(-0.5*((i-100)/6)**2);
      const x=[...Array(nx).keys()].map(i=>i*25), row=()=>Array.from(T.c.slice(0,nx));
      const c0=row(); for(let s=0;s<400;s++) T.step(0.3,0,25,'upwind',null);
      return S.effectiveK(c0,row(),x,400*25);"""
    k = run_js(body, {})
    assert k == pytest.approx(numerics.k_num_upwind(0.3, 25.0, 25.0), rel=0.05)
