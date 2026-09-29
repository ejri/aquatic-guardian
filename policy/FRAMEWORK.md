# The Aquatic Guardian Framework

**Version 0.1, public consultation draft, 29 September 2026.** Text licensed CC BY 4.0.

A plug-in module that adds the aquatic, ecological and animal-welfare footprint of data centres to the regulation governments are already writing. It does not create a new regime. It supplies definitions, metrics, screening methods, permit conditions and review triggers that slot into existing bills, rating schemes, permits and procurement rules.

This version builds on *Governing the Ocean Server Farm* (Elchami, Kaplan and Daher, Sentient Futures, April 2026), which mapped the governance gap for offshore compute and identified four stressors: thermal discharge, electromagnetic fields, underwater noise and chemical releases. Version 0.1 adds cooling-water intake and the welfare of individual animals, and gives each stressor a measurable, reportable metric.

## 1. Why a module and not a new law

AI compute is scaling fast. The IEA projects data-centre electricity use roughly doubling from 485 TWh in 2025 to about 950 TWh in 2030. Nearly all of that electricity leaves the building as low-grade heat. Where facilities cool with seawater or surface water, or sit in the water, that heat and the water drawn to carry it reach animals directly.

Legislatures are already moving on data centres, but for energy, cost and community reasons. The US AI Data Center Moratorium Act (S.4214 / H.R.9442) requires reporting of "wastewater discharge and thermal outputs" without defining either. The EU has adopted a rating scheme built on energy, water and waste-heat indicators, none of which measure heat discharged to water or animals killed at an intake. British Columbia now allocates power to data centres competitively and scores environmental impact without an aquatic metric. Each of these is a slot this framework is designed to fill.

## 2. Principles

1. **Heat discharged to water is pollution before it is a resource.** UNCLOS Article 1(1)(4) includes the introduction of "energy" in its definition of marine pollution; Phase 1 sets out why ITLOS Advisory Opinion No. 31 (21 May 2024) supports reading that to cover heat from offshore infrastructure. Canada's Fisheries Act already defines water changed by heat as a potentially deleterious substance.
2. **Reuse counts only if it happens before discharge.** Diluted heat has almost no useful exergy. Heat recovered from the cooling loop is reuse; warm water released to a bay is discharge, whatever happens to it afterwards.
3. **Assess critical conditions, not averages.** Mixing-zone compliance is judged at slack water, low-percentile currents and summer-maximum ambient temperature, as regulators already do for power plants.
4. **Count individuals as well as populations.** Environmental law protects populations; animals suffer as individuals. Where there is a realistic possibility of sentience, affected animals are reported by taxon, life stage and evidence tier alongside population metrics, never collapsed into one weighted score.
5. **Label uncertainty honestly.** Screening results are marked as screening results. Species thresholds and welfare parameters that have not been expert-reviewed are marked as placeholders and cannot support a decision.
6. **Attach, don't replace.** Every requirement names the existing instrument it plugs into, and uses that instrument's own definitions and thresholds wherever they exist.
7. **Indigenous rights are a precondition.** Siting in or near Indigenous waters requires consultation to the standard of the applicable law, including UNDRIP-aligned statutes such as BC's DRIPA and treaty-reserved fishing rights in the US.

## 3. Coverage

| Tier | Which facilities | What applies |
|---|---|---|
| A. Disclosure | Any data centre of 500 kW IT or more that withdraws or discharges surface water or seawater, or is sited in, on or under water | Layer 1 |
| B. Assessment | Tier A facilities with design intake above 2 MGD (0.088 m³/s), or more than 3 MW of heat to water, or within or adjacent to a protected area, critical habitat or Essential Fish Habitat | Layers 1 to 5 |
| C. Enhanced | Submerged or floating facilities; facilities in estuaries or enclosed bays; any facility supplying heat to aquaculture | Layers 1 to 5, plus the enhanced conditions in section 5 |

The 500 kW floor matches EU Energy Efficiency Directive Article 12 reporting. The 2 MGD trigger matches US CWA §316(b); a once-through facility crosses it at roughly 3 to 4 MW of heat rejected at a 10 K rise.

## 4. The five layers

The layers are sequential: each one supplies the evidence the next one needs.

### Layer 1. Disclosure

Operators report, per facility and per reporting period, the Aquatic Disclosure Record defined in `schemas/aquatic-disclosure.schema.json`:

- heat rejected, heat to water, and heat reused before discharge (energy reuse factor, ISO/IEC 30134-6);
- discharge temperature rise (mean, 95th percentile, maximum);
- design and actual intake flow, cooling fraction and through-screen velocity;
- impinged and entrained organisms by taxon, life stage and sentience evidence tier;
- biocides, antifouling agents, corrosion inhibitors and coolants, in kilograms of active ingredient;
- underwater noise source level and band;
- cable voltage, current type, burial depth and field strength;
- freshwater withdrawal and consumption (WUE, ISO/IEC 30134-9).

The record is machine-readable and published. Field definitions are in `docs/METRICS.md`; the crosswalk to S.4214/H.R.9442 and EU Delegated Regulation 2024/1364 is in `docs/CROSSWALK.md`.

### Layer 2. Assessment

Before approval, Tier B and C facilities submit:

- a near-field and far-field thermal assessment at critical design conditions, using a recognised model (Visual Plumes UM3, NRFIELD, CORMIX or equivalent) with the grid resolution and numerical scheme reported;
- an intake assessment against the jurisdiction's intake rules;
- a receptor assessment covering protected species, Essential Fish Habitat or equivalent, and taxa in sentience tier 1;
- cumulative effects with other thermal discharges and with projected climate warming;
- for Tier C, the four Phase 1 stressors in full.

The open-source screening tool in this repository can support scoping; it does not replace these studies.

### Layer 3. Permit conditions

Model conditions are in `policy/model-language/permit-conditions.md`. The core set:

- closed-loop or air-rejected cooling as the default; once-through cooling only where the operator shows it is the least-harm option for the site;
- a numeric temperature increment at a defined mixing-zone edge, from the jurisdiction's own rule;
- a through-screen velocity no greater than 0.5 ft/s (0.15 m/s), or the jurisdiction's equivalent;
- controlled ramp-down on shutdown to prevent cold shock to animals attracted to the outfall;
- limits on biocides and antifouling agents, with copper-free fouling control in sensitive habitat;
- a reopener if monitoring exceeds any trigger in Layer 5.

### Layer 4. Monitoring

- continuous temperature at the outfall, the mixing-zone edge and a reference site;
- dissolved oxygen at the mixing-zone edge in warm months;
- impingement and entrainment sampling to the jurisdiction's protocol, reported by taxon, life stage and tier;
- occupancy monitoring (camera, BRUV or eDNA) analysed with detection-probability correction, because turbidity-driven detection failure otherwise looks like ecological impact;
- public release of monitoring data within 90 days.

### Layer 5. Adaptive management

Triggers that reopen the permit or require load reduction:

- the temperature increment exceeded at the mixing-zone edge on more than a set number of days in a season;
- a cold-shock or mass-mortality event;
- a detection-corrected decline in occupancy of a tier 1 taxon relative to the reference site;
- for aquaculture reuse, breach of the named welfare standard.

Load reduction can be met by shifting compute to another site, which data centres can do in minutes and power plants cannot. This makes adaptive thermal management unusually practical for data centres.

## 5. Enhanced conditions for Tier C

- **Submerged and floating facilities:** decommissioning plan and full financial assurance at commissioning; no deployment in marine protected areas or critical habitat; baseline survey of at least one full year before deployment.
- **Estuaries and enclosed bays:** the intake proportional-flow test (for example 40 CFR 125.84) and a flushing-time assessment.
- **Heat to aquaculture:** a named welfare standard for each species (for example RSPCA Assured, ASC, or a species-specific EFSA opinion); stocking density, water quality, mortality and stunning method reported; reuse counts toward any energy reuse target only when the welfare standard is met. Supplying heat to a farm that keeps more animals in poor conditions is not an environmental benefit.

## 6. The sentience dimension

| Tier | Taxa | Basis |
|---|---|---|
| 1 | Vertebrates (fishes, marine mammals, seabirds, sea turtles), cephalopod molluscs, decapod crustaceans | UK Animal Welfare (Sentience) Act 2022; Birch et al. (2021); New York Declaration on Animal Consciousness (2024) |
| 2 | Other crustaceans, gastropods and other invertebrates with behavioural evidence | NY Declaration: "realistic possibility" in many invertebrates; precautionary reporting and research priority |
| 3 | Taxa without a current evidence basis for regulatory use (for example sponges, cnidarians; bivalves are contested) | Reported for ecology, not welfare |

Eggs, embryos and early larvae, which make up most entrainment losses, are reported as their own rows. Whether they are sentient is unresolved, and merging them with juveniles and adults would either inflate or erase the welfare signal.

## 7. What this framework does not do

- It does not rank data-centre siting against terrestrial alternatives, which have their own water, energy and community impacts.
- It does not set species thresholds. It points to each jurisdiction's criteria and marks unreviewed values as placeholders.
- It does not constitute legal advice. Applicability of any statute to a specific facility is a legal determination.

## 8. How the framework is maintained

Versions are numbered and dated. Changes are proposed as public pull requests, reviewed by a technical steering group that includes an independent coastal engineer and a fish-welfare scientist, and recorded in `CHANGELOG.md`. Comments on this draft are open until a closing date set by the steering group and published on the project website.
