"""Sentience-aware impact reporting.

Environmental law protects populations; §316(b) monitoring already counts
individuals. This module reports affected individuals by evidence tier and
life stage *alongside* population metrics. It never collapses them into a
single weighted score: the weights would be false precision.

Tiers:
  1 - legally recognised or strong evidence: vertebrates (fishes, marine
      mammals, birds, reptiles), cephalopod molluscs, decapod crustaceans
      (UK Animal Welfare (Sentience) Act 2022; Birch et al. 2021 LSE review;
      New York Declaration on Animal Consciousness 2024).
  2 - realistic possibility (NY Declaration 'many invertebrates'): other
      crustaceans, gastropods, and other invertebrates with behavioural
      evidence. Precautionary reporting; research priority.
  3 - no current evidence basis for regulatory use (e.g. sponges, cnidarians,
      bivalves: contested).
Life stage is reported separately. Whether fish embryos and early larvae
(most entrainment losses) are sentient is unresolved; they are reported as a
distinct row, never merged with juveniles or adults.
"""
from __future__ import annotations

TAXON_TIER = {
    "fish": 1, "marine_mammal": 1, "seabird": 1, "sea_turtle": 1,
    "cephalopod": 1, "decapod": 1,
    "other_crustacean": 2, "gastropod": 2, "other_invertebrate": 2,
    "bivalve": 3, "cnidarian": 3, "sponge": 3,
}
LIFE_STAGES = ("egg_embryo", "larva", "juvenile", "adult")


def tier(taxon: str) -> int:
    return TAXON_TIER.get(taxon, 2)


def impact_table(counts: list[dict]) -> list[dict]:
    """counts: [{'taxon': 'fish', 'life_stage': 'larva', 'pathway': 'entrainment', 'n': 1200}]"""
    rows = {}
    for c in counts:
        key = (tier(c["taxon"]), c["taxon"], c["life_stage"], c["pathway"])
        rows[key] = rows.get(key, 0) + int(c["n"])
    return [{"tier": k[0], "taxon": k[1], "life_stage": k[2], "pathway": k[3], "n": v}
            for k, v in sorted(rows.items())]


def required_reporting(cooling_type: str, marine: bool, aquaculture_reuse: bool) -> list[str]:
    items = []
    if cooling_type != "closed_loop_air":
        items += ["impingement counts by taxon, life stage and tier",
                  "entrainment estimates by taxon and life stage (eggs/larvae separate)",
                  "fish aggregation and cold-shock events at the outfall"]
    if marine:
        items += ["marine mammal and sea turtle interaction log (MMPA/ESA/SARA)"]
    if aquaculture_reuse:
        items += ["named welfare standard for any farmed species using reused heat",
                  "stocking density, water quality and mortality by species",
                  "stunning and slaughter method"]
    return items
