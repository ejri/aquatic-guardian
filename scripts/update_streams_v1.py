#!/usr/bin/env python3
"""Apply verified YouTube embeds + ONC schedule text to site/data/streams.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "site" / "data" / "streams.json"

# Confirmed via YouTube oEmbed on 2026-10-17
YOUTUBE = {
    "anacapa": {
        "video_id": "aaUERtNMn7o",
        "title": "Anacapa Island Cove - Channel Islands National Park Cams powered by EXPLORE.org",
        "url": "https://www.youtube.com/live/aaUERtNMn7o",
        "explore": "https://explore.org/livecams/oceans/channel-islands-national-park-anacapa-ocean",
        "note": "YouTube live via Explore Oceans; NPS Ocean Webcam partnership (Anacapa landing cove).",
        "verify": False,
    },
    "bonaire": {
        "video_id": "wANBWGe8zhI",
        "title": "Bonaire Underwater Cam powered by EXPLORE.org",
        "url": "https://www.youtube.com/watch?v=wANBWGe8zhI",
        "explore": "https://explore.org/livecams/oceans/bonaire-underwater",
        "note": "YouTube live via Explore Oceans.",
        "verify": False,
    },
    "frying-pan": {
        "video_id": "og8bbxl0iW8",
        "title": "Shark Cam powered by EXPLORE.org",
        "url": "https://www.youtube.com/live/og8bbxl0iW8",
        "explore": "https://explore.org/livecams/oceans/shark-cam",
        "note": "Underwater Shark Cam beneath Frying Pan Tower (~34 mi offshore Cape Fear). Related Explore Oceans lives: Barracuda Cam 9kMqCUu3_YY, Ocean Cam pW_S5RTdnSQ.",
        "verify": False,
    },
    "coral-city": {
        "video_id": "7i8ARjIeM2k",
        "title": "Coral City Camera (Miami's Free-Range Aquarium Underwater Livestream)",
        "url": "https://www.youtube.com/live/7i8ARjIeM2k",
        "explore": "https://www.coralcitycamera.com/",
        "note": "Coral Morphologic YouTube live from PortMiami riprap (~3 m).",
        "verify": False,
    },
}

# Schedules transcribed from https://www.oceannetworks.ca/multimedia/live-cameras/ (2026-10-17)
ONC = {
    "onc-folger": {
        "name": "Folger Pinnacle, Barkley Sound",
        "schedule": "Camera is on for 5 minutes every hour on the hour (Ocean Networks Canada).",
        "note": "Watch on Oceans 3.0 / ONC Live Cameras; timed clips, not a continuous YouTube embed.",
        "status": "scheduled",
        "verify": False,
    },
    "onc-endeavour": {
        "name": "Tempo Mini — Main Endeavour Field",
        "schedule": "Camera records for four minutes every four hours (Ocean Networks Canada).",
        "note": "Hydrothermal vent camera on ONC Live Cameras. Related: Endeavour Mothra is on for four minutes every four hours.",
        "status": "scheduled",
        "verify": False,
    },
    "onc-campbell": {
        "name": "Campbell River community observatory",
        "schedule": "Offline until further notice (Ocean Networks Canada Live Cameras list, 2026-10-17).",
        "note": "Listed offline on ONC Live Cameras with Barkley Canyon Mid-East, Node Fish Acoustics, and Barkley Upper Slope.",
        "status": "offline",
        "verify": False,
    },
    "onc-kitamaat": {
        "name": "Kitamaat Village community observatory",
        "schedule": "Camera is on for five minutes every hour on the hour (Ocean Networks Canada).",
        "note": "ONC + Haisla Nation community observatory; watch on ONC Live Cameras.",
        "status": "scheduled",
        "verify": False,
    },
    "onc-digby": {
        "name": "Digby Island, Prince Rupert",
        "schedule": "Camera is on for five minutes every hour on the hour (Ocean Networks Canada).",
        "note": "Watch on ONC Live Cameras.",
        "status": "scheduled",
        "verify": False,
    },
    "onc-barkley-canyon": {
        "name": "Barkley Canyon Axis",
        "schedule": "Camera is on for five minutes every hour on the hour (Ocean Networks Canada).",
        "note": "Barkley Canyon Axis is live on schedule. Mid-East, Node Fish Acoustics, and Upper Slope remain offline until further notice.",
        "status": "scheduled",
        "verify": False,
        "depth_m": None,
    },
    "onc-cambridge": {
        "schedule": "Short scheduled clips via ONC community observatories (confirm current slot on Live Cameras).",
        "note": "Arctic coastal camera; watch on ONC Live Cameras when the schedule is active.",
        "verify": True,
    },
}

ONC_URL = "https://www.oceannetworks.ca/multimedia/live-cameras/"

# Extra ONC cameras from the same page (not previously catalogued)
NEW_ONC = [
    {
        "kind": "scheduled",
        "embed": False,
        "verify": False,
        "analysis_permission": "not requested",
        "species": ["deep-sea fauna"],
        "depth_m": None,
        "schedule": "Camera is on for five minutes every hour on the hour (Ocean Networks Canada).",
        "coops": None,
        "iwls_code": None,
        "note": "Watch on ONC Live Cameras.",
        "id": "onc-cascadia",
        "name": "Cascadia Basin",
        "operator": "Ocean Networks Canada",
        "region": "deep-sea",
        "lat": 47.76,
        "lon": -127.76,
        "ecosystem": "Abyssal Cascadia Basin",
        "provider": {"type": "external", "url": ONC_URL},
        "status": "scheduled",
        "sal_psu": 34.5,
    },
    {
        "kind": "scheduled",
        "embed": False,
        "verify": False,
        "analysis_permission": "not requested",
        "species": ["nearshore fauna"],
        "depth_m": None,
        "schedule": "Camera is on for five minutes every hour on the hour (Ocean Networks Canada).",
        "coops": None,
        "iwls_code": None,
        "note": "Watch on ONC Live Cameras.",
        "id": "onc-china-creek",
        "name": "China Creek",
        "operator": "Ocean Networks Canada",
        "region": "ne-pacific",
        "lat": 48.93,
        "lon": -125.02,
        "ecosystem": "Barkley Sound nearshore",
        "provider": {"type": "external", "url": ONC_URL},
        "status": "scheduled",
        "sal_psu": 31.0,
    },
    {
        "kind": "scheduled",
        "embed": False,
        "verify": False,
        "analysis_permission": "not requested",
        "species": ["fjord fauna"],
        "depth_m": None,
        "schedule": "Camera is on for five minutes every hour on the hour (Ocean Networks Canada).",
        "coops": None,
        "iwls_code": None,
        "note": "Watch on ONC Live Cameras.",
        "id": "onc-hartley-bay",
        "name": "Hartley Bay",
        "operator": "Ocean Networks Canada",
        "region": "ne-pacific",
        "lat": 53.42,
        "lon": -129.25,
        "ecosystem": "Gitga'at territory, Douglas Channel area",
        "provider": {"type": "external", "url": ONC_URL},
        "status": "scheduled",
        "sal_psu": 28.0,
    },
    {
        "kind": "scheduled",
        "embed": False,
        "verify": False,
        "analysis_permission": "not requested",
        "species": ["nearshore fauna"],
        "depth_m": None,
        "schedule": "Camera is on for five minutes every hour on the hour (Ocean Networks Canada).",
        "coops": None,
        "iwls_code": None,
        "note": "Atlantic community observatory; watch on ONC Live Cameras.",
        "id": "onc-holyrood",
        "name": "Holyrood Bay",
        "operator": "Ocean Networks Canada",
        "region": "north-atlantic",
        "lat": 47.39,
        "lon": -53.14,
        "ecosystem": "Newfoundland coastal",
        "provider": {"type": "external", "url": ONC_URL},
        "status": "scheduled",
        "sal_psu": 31.0,
    },
    {
        "kind": "scheduled",
        "embed": False,
        "verify": False,
        "analysis_permission": "not requested",
        "species": ["vent fauna"],
        "depth_m": 2200,
        "schedule": "Camera is on for four minutes every four hours (Ocean Networks Canada).",
        "coops": None,
        "iwls_code": None,
        "note": "Endeavour Mothra hydrothermal camera on ONC Live Cameras.",
        "id": "onc-mothra",
        "name": "Endeavour Mothra",
        "operator": "Ocean Networks Canada",
        "region": "deep-sea",
        "lat": 47.92,
        "lon": -129.11,
        "ecosystem": "Hydrothermal vents, Endeavour segment",
        "provider": {"type": "external", "url": ONC_URL},
        "status": "scheduled",
        "sal_psu": 34.6,
    },
]


def as_youtube(s: dict, meta: dict) -> None:
    s["embed"] = True
    s["verify"] = meta["verify"]
    s["note"] = meta["note"]
    s["provider"] = {
        "type": "youtube_video",
        "video_id": meta["video_id"],
        "url": meta["url"],
        "explore_url": meta.get("explore"),
        "title": meta["title"],
    }


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    data["as_of"] = "2026-10-17"
    data["note"] = (
        "Status changes daily. YouTube embeds confirmed via oEmbed where listed. "
        "ONC schedules transcribed from oceannetworks.ca/multimedia/live-cameras/. "
        "Update via scripts/healthcheck_streams.py and scripts/update_streams_v1.py."
    )
    by_id = {s["id"]: s for s in data["streams"]}
    for sid, meta in YOUTUBE.items():
        as_youtube(by_id[sid], meta)
    # Beluga is seasonal events, not a continuous live — keep external, mark clearly
    bel = by_id["beluga"]
    bel["embed"] = False
    bel["verify"] = False
    bel["note"] = (
        "Seasonal Explore.org Beluga Boat tours (Churchill River), not a 24/7 stream. "
        "Off-season: highlights only. See explore.org/livecams/beluga-whales/beluga-boat-cam-underwater."
    )
    bel["schedule"] = "Summer boat tours only (tide-dependent); not continuous"
    bel["status"] = "seasonal"
    for sid, patch in ONC.items():
        s = by_id[sid]
        for k, v in patch.items():
            s[k] = v
        s["provider"] = {"type": "external", "url": ONC_URL}
        s["embed"] = False
    existing = set(by_id)
    for row in NEW_ONC:
        if row["id"] not in existing:
            data["streams"].append(row)
    PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"updated {PATH} ({len(data['streams'])} streams)")


if __name__ == "__main__":
    main()
