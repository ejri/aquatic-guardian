# California Thermal Plan — new coastal discharges (primary text)

**Document:** Water Quality Control Plan for Control of Temperature in the Coastal
and Interstate Waters and Enclosed Bays and Estuaries of California (Thermal Plan).

**Issuer:** State Water Resources Control Board (SWRCB).

**Document date / provenance:** Plan text as published by the SWRCB (revises and
supersedes the policy adopted 7 January 1971, revised 13 October 1971 and
5 June 1972). PDF retrieved from
https://www.waterboards.ca.gov/water_issues/programs/ocean/docs/wqplans/thermpln.pdf
(accessed 2026-09-29). Footer of the published file: `PZENTNER:shalbert:1-16-98`.

**Legal status:** Enacted water-quality control plan (statewide); Regional Boards
may grant §316(a) exceptions with State Board concurrence.

## Exact text transcribed — Specific Water Quality Objectives, §3 Coastal Waters, B. New discharges

> B. New discharges
>
> (1) Elevated temperature wastes shall be discharged to the open ocean away from
> the shoreline to achieve dispersion through the vertical water column.
>
> (2) Elevated temperature wastes shall be discharged a sufficient distance from
> areas of special biological significance to assure the maintenance of natural
> temperature in these areas.
>
> (3) The maximum temperature of thermal waste discharges shall not exceed the
> natural temperature of receiving waters by more than 20°F.
>
> (4) The discharge of elevated temperature wastes shall not result in increases
> in the natural water temperature exceeding 4°F at (a) the shoreline, (b) the
> surface of any ocean substrate, or (c) the ocean surface beyond 1,000 feet from
> the discharge system. The surface temperature limitation shall be maintained at
> least 50 percent of the duration of any complete tidal cycle.
>
> (5) Additional limitations shall be imposed when necessary to assure protection
> of beneficial uses.

## Values used by the library

| Quantity | Plan text | Library (`criteria.ca_thermal_plan_new_coastal`) |
|---|---|---|
| Max discharge rise | 20°F above natural | `max_discharge_delta_k` = 20 × 5/9 K |
| Receiving-water rise | 4°F at shoreline / substrate / surface beyond 1,000 ft | `allowed_increment_k` = 4 × 5/9 K |
| Distance | 1,000 feet | parsed by `tests/test_primary_sources.py` |
