# Bower & Bidwell (1978) seawater NH₃ — provenance for `bower_bidwell_1978.csv`

Primary paper: Bower, C.E. & Bidwell, J.P. (1978). Ionization of ammonia in
seawater: effects of temperature, pH, and salinity. *Journal of the Fisheries
Research Board of Canada* **35**: 1012–1016.
https://doi.org/10.1139/f78-165

The PDF paywall was not opened in this repository. Values below are taken from
named secondary sources that attribute the numbers to Bower & Bidwell or state
numerical agreement with that table. Status in `docs/VERIFICATION.md` is therefore
**Published value (secondary)** until someone pastes the printed percents from
pages 1012–1016 of the primary PDF.

## Rows used

| T °C | pH | S | % NH₃ | Source |
|---|---|---|---|---|
| 20 | 8.0 | 34 | **2.98** | LaMotte Salt Water Aquaculture kit manual (Code 3635-05): “Seawater values from Bower and Bidwell (1978). Salinity for Seawater values = 34 ppt” |
| 25 | 8.0 | 34 | **4.28** | Same LaMotte table, seawater column at pH 8.0 / 25 °C |
| 25 | 8.0 | 30 | **4.39** | Florida DEP Chemistry Lab Methods Manual Appendix III, Table 3 (pH 8.0): ratio total NH₄-N / NH₃-N = **22.8** at 25 °C, S = 30‰ → percent = 100/22.8. Tables are from Spotte & Adams (1983), who state close agreement with Bower & Bidwell (1978) Whitfield-based values |

## Cross-check

At 25 °C, pH 8.0, S = 35‰ the same Spotte Table 3 gives ratio **23.6** → **4.24%**, matching the Florida DEP worked example that cites that cell. The library (Emerson + Khoo) gives ≈ 4.26% at those conditions.
