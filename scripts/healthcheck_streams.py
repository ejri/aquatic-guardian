"""Nightly stream health check: updates status fields in site/data/streams.json
and writes a markdown report for review. Never swaps a stream id on its own:
replacement live videos on the same channel are proposed in the report.

    YOUTUBE_API_KEY=... python scripts/healthcheck_streams.py
Quota: 1 unit per videos.list batch, 100 per search.list (only for ended streams
with a known channel id).
"""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "site" / "data" / "streams.json"
KEY = os.environ.get("YOUTUBE_API_KEY")


def get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "AquaticGuardianHealthcheck/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def yt(path, **q):
    q["key"] = KEY
    return json.loads(get("https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(q))[1])


def main():
    data = json.loads(REG.read_text())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    report = [f"# Stream health check {now}", ""]
    yts = [s for s in data["streams"] if s["provider"]["type"] == "youtube_video"]
    if KEY and yts:
        items = {v["id"]: v for v in yts and yt("videos", part="liveStreamingDetails,status,snippet", id=",".join(s["provider"]["video_id"] for s in yts)).get("items", [])}
        for s in yts:
            v = items.get(s["provider"]["video_id"])
            if not v:
                s["status"] = "removed"
            else:
                live = v.get("liveStreamingDetails", {})
                s["status"] = "live" if live.get("actualStartTime") and not live.get("actualEndTime") else ("ended" if live.get("actualEndTime") else "not live")
                s["embed"] = bool(v.get("status", {}).get("embeddable", True))
            s["checked"] = now
            if s["status"] in ("removed", "ended") and s["provider"].get("channel_id"):
                cands = yt("search", part="snippet", channelId=s["provider"]["channel_id"], eventType="live", type="video", maxResults=10).get("items", [])
                report.append(f"- **{s['name']}** is {s['status']}. Live on the same channel now: " +
                              (", ".join(f"`{c['id']['videoId']}` {c['snippet']['title']}" for c in cands) or "none") + ". Pick the matching camera by hand.")
            elif s["status"] != "live":
                report.append(f"- **{s['name']}** is {s['status']}.")
    elif not KEY:
        report.append("- YOUTUBE_API_KEY not set; YouTube entries not checked.")
    for s in data["streams"]:
        if s["provider"]["type"] != "external" or s.get("status") == "offline":
            continue
        try:
            code, _ = get(s["provider"]["url"])
            s["page_status"] = code
        except Exception as e:  # noqa: BLE001
            s["page_status"] = str(e)[:80]
            report.append(f"- **{s['name']}** operator page unreachable: {s['page_status']}")
        s["checked"] = now
    data["as_of"] = now[:10]
    REG.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    (ROOT / "streams-health.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    sys.exit(main())
