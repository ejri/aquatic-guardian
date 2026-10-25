# Live streams: catalogue, permissions, maintenance

`site/data/streams.json` holds ~48 streams and 7 ocean data-centre sites (as of 2026-10-17). Each stream has a
`kind` (open ocean, aquarium, scheduled clips, expedition, surface view), a `verify` flag for entries we could
not confirm live or embeddable, and an `analysis_permission` field.

**Explore.org Oceans** ([livecams/oceans](https://explore.org/livecams/oceans/)): Utopia Village reef wall and dock cams,
Anacapa, Bonaire, Frying Pan Shark Cam, USC Wrigley Catalina, Homosassa manatees, Aquarium of the Pacific exhibits,
and OrcaLab / sea-lion cams play in the privacy-enhanced YouTube embed when a live id is confirmed. Refresh with
`python scripts/integrate_explore_oceans.py`.

Ocean Networks Canada cameras follow the schedules on [ONC Live Cameras](https://www.oceannetworks.ca/multimedia/live-cameras/)
and open on the operator site (timed clips, not continuous YouTube).

## Rules the site follows

- **Embed, don't extract.** YouTube streams play in YouTube's privacy-enhanced player, unmodified. The site
  never reads pixels from a YouTube iframe (browsers block it; YouTube API Services policies prohibit separating
  or modifying audio or video components). In-browser analysis uses a tab the visitor chooses to share, or a
  local file.
- **Server analysis needs written permission.** `relay/permitted_streams.json` starts a vision worker only for
  entries with `permission.status = "granted"`, a `granted_by` and a `date`. The relay code enforces this.
- **Label what it is.** Aquarium cameras are labelled as aquariums; unverified entries are marked.
- **SkylineWebcams** feeds need a licence before embedding; they are listed with a link only.

## Requesting permission (template)

> Subject: Permission to compute fish-behaviour statistics from your [camera name] stream
>
> We run Aquatic Guardian (Sentient Futures), an open, non-commercial project on how data centres affect
> marine life. We would like to analyse your [camera] stream on our server to publish live, aggregate behaviour
> statistics (number of animals in view, swimming speed, schooling) next to your embedded player, credited
> to you. We would not store, re-stream or redistribute frames, and would stop on request.
> Could you confirm whether this is acceptable, and whether you can offer an HLS endpoint with CORS enabled for
> our domain (which would let visitors' browsers run the analysis directly)?

Suggested first contacts: explore.org (Utila, Bonaire, Frying Pan Tower, Anacapa), Coral Morphologic (Coral City
Camera), The MEGA Lab / Aqualink (Kona), Ocean Networks Canada (Oceans 3.0 archive and scheduled cameras),
James Cook University (Orpheus Island), Monterey Bay Aquarium.

## Regions without a verified stream

Southeast Asia, Japan and East Asia, Southern Africa, and salmon farms. New Zealand and Antarctica have no
continuous public feed either (expedition streams only). Suggestions go through the "Suggest a stream" link on
each empty region, which opens a GitHub issue.

## Keeping it current

Streams restart under new video ids. `scripts/healthcheck_streams.py` runs nightly (GitHub Actions,
`YOUTUBE_API_KEY` secret), updates `status` and `checked`, and opens a pull request with a report that proposes
replacement live videos on the same channel. It never swaps an id by itself: a person confirms the camera.
