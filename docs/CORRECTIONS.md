# Technical corrections adopted in version 0.1

Six changes from the research fact-check (29 September 2026), each implemented in the library and covered by a test.

**1. Per-port and per-length fluxes.** Point-plume laws take the flow, momentum and buoyancy of one port; line-plume laws take flux per unit length (q = Q_T/L). Feeding total diffuser flow into a point-plume law understates dilution by N^(2/3); for 10 ports that is 4.6-fold. The regime is chosen by port spacing over depth (Tian, Roberts & Daviero 2004). *Module:* `plume.py`. *Test:* `test_total_flow_substitution_error_is_n_two_thirds`.

**2. Tidal excursion per half-cycle.** For u = U sin ωt, the flood or ebb excursion is 2U/ω. Over whole cycles the oscillation cancels and only residual drift remains. The 10.7 km excursion in the earlier model implies a peak current of about 0.75 m/s, typical of straits and passes in the Salish Sea but high for open coast (0.1 to 0.3 m/s). Take U from station data. *Module:* `tidal.py`.

**3. Numerical diffusion.** First-order upwind adds |u|Δx/2 (1−C). At 25 m that is 2 to 4 m²/s for typical tidal currents, larger than Okubo's physical diffusivity at every scale below about 3 km. The earlier model therefore over-dispersed the plume and under-predicted peak temperature exactly where the "heat is gone within 1 km" result was drawn. Use a flux-limited scheme (`numerics.advect_diffuse_1d(..., scheme="tvd")`) or report K_num beside K_phys. *Tests:* N-2 to N-4.

**4. Critical design conditions.** Mixing-zone compliance is evaluated at slack water or a low-percentile current, summer-maximum ambient temperature and maximum discharge, not at a steady mean current. The screening tool uses the stagnant near-field limit, which is the slack-water case.

**5. Ammonia speciation.** Use the Emerson et al. (1975) pKa with the seawater ionic-strength correction, and evaluate US freshwater criteria with the EPA 2013 equations. EPA saltwater criteria date from 1989 and were not revised in 2013; CCME has no marine ammonia guideline.

**6. Open-water heat reuse.** Replace "beneficial reuse of waste heat in open water is structurally incoherent because tidal dispersion removes heat within ~1 km" with: *Beneficial reuse of data-centre heat is only practical before discharge, at source temperature, through closed-loop heat exchange. Heat discharged to open water should be treated as a regulated thermal load, not a resource.* The thermodynamic point stands; the 1 km figure depended on the site and on numerical diffusion.
