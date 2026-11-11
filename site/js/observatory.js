/* observatory.js: the #/observe route. Registers with the site router
 * (window.AGU) and loads nothing from the network until the route opens. */
(function () {
  "use strict";
  var U = window.AGU, $ = U.$, $$ = U.$$, fmt = U.fmt, esc = U.esc, P = window.Plumes2, OD = window.OceanData, V = window.Vision;
  var REG = null, WORLD = null, ST = { stream: null, ocean: null, engine: null, ws: null, history: [], site: null, lastRun: null, ytReady: null, player: null, hls: null, video: null, region: "all", scrolled: false };
  var HLS_CDN = "https://cdn.jsdelivr.net/npm/hls.js@1.5.17/dist/hls.min.js";
  var EE = { A1: 1.340264, A2: -0.081106, A3: 0.000893, A4: 0.003796 };
  var KIND = { open_ocean: "Open ocean", aquarium: "Aquarium", expedition: "Expedition", scheduled: "Scheduled clips", surface: "Surface view" };

  /* Equal Earth projection → SVG pixel (matches site/data/world.json). */
  function project(lon, lat) {
    var M = Math.sqrt(3) / 2, l = lon * Math.PI / 180, p = lat * Math.PI / 180, th = Math.asin(M * Math.sin(p)), t2 = th * th, t6 = t2 * t2 * t2;
    var x = 2 * Math.sqrt(3) * l * Math.cos(th) / (3 * (9 * EE.A4 * t6 * t2 + 7 * EE.A3 * t6 + 3 * EE.A2 * t2 + EE.A1));
    var y = th * (EE.A1 + EE.A2 * t2 + t6 * (EE.A3 + EE.A4 * t2));
    return [(x / WORLD.xmax + 1) * WORLD.width / 2, (1 - y / WORLD.ymax) * WORLD.height / 2];
  }

  /* ------------------------------------------------------------ init */
  U.inits.observe = function (sub) {
    Promise.all([
      fetch("data/streams.json", { cache: "no-store" }).then(function (r) { return r.json(); }),
      fetch("data/world.json", { cache: "no-store" }).then(function (r) { return r.json(); })
    ]).then(function (a) {
      REG = a[0]; WORLD = a[1];
      drawMap(); drawRegions(); drawGallery(); deadlineBanner(); bindTabs(); bindVision(); bindScenario(); bindResearch();
      var nYt = REG.streams.filter(function (s) { return s.embed && s.provider && s.provider.type === "youtube_video"; }).length;
      $("#obs-status").innerHTML = REG.streams.length + " cameras · " + nYt + " play on this page · click a pin or card";
      select(sub && byId(sub) ? sub : (sub && site(sub) ? null : "utila-top"));
      if (sub && site(sub)) openSite(sub);
    }).catch(function (e) { $("#obs-status").textContent = "The stream list did not load (" + e.message + "). Reload the page to try again."; });
  };
  U.onRoute.observe = function (sub) { if (REG && sub) { if (byId(sub)) select(sub); else if (site(sub)) openSite(sub); } if (!sub || !REG) return; };
  function byId(id) { return REG && REG.streams.filter(function (s) { return s.id === id; })[0]; }
  function site(id) { return REG && REG.sites.filter(function (s) { return s.id === id; })[0]; }

  /* ------------------------------------------------------------- map */
  function drawMap() {
    var svg = $("#obs-map-svg");
    if (!svg || !WORLD) return;
    svg.setAttribute("viewBox", "0 0 " + WORLD.width + " " + WORLD.height);
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.innerHTML =
      '<defs>' +
      '<linearGradient id="obsOceanGrad" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0%" stop-color="#0a4a5c"/><stop offset="55%" stop-color="#053142"/><stop offset="100%" stop-color="#031820"/></linearGradient>' +
      '<radialGradient id="obsGlow" cx="35%" cy="30%" r="65%">' +
      '<stop offset="0%" stop-color="rgba(90,180,200,0.22)"/><stop offset="100%" stop-color="rgba(0,0,0,0)"/></radialGradient>' +
      '<filter id="obsLandSoft" x="-2%" y="-2%" width="104%" height="104%">' +
      '<feDropShadow dx="0" dy="0.6" stdDeviation="0.8" flood-color="#000" flood-opacity="0.35"/></filter>' +
      '</defs>' +
      '<rect width="' + WORLD.width + '" height="' + WORLD.height + '" fill="url(#obsOceanGrad)"/>' +
      '<rect width="' + WORLD.width + '" height="' + WORLD.height + '" fill="url(#obsGlow)"/>' +
      '<path class="m-ocean" d="' + WORLD.outline + '" fill="url(#obsOceanGrad)"/>' +
      '<path class="m-grat" d="' + WORLD.graticule + '"/>' +
      '<path class="m-land" d="' + WORLD.land + '" filter="url(#obsLandSoft)"/>';
    var layer = $("#obs-markers"); if (!layer) return;
    layer.innerHTML = "";
    REG.streams.forEach(function (s) {
      var p = project(s.lon, s.lat), b = document.createElement("button");
      var off = /^(offline|removed|ended)$/.test(s.status || "");
      var t = thumbUrl(s);
      b.type = "button";
      b.className = "mk pin k-" + s.kind + (off ? " off" : "") + (s.embed ? " embed" : "");
      b.style.left = (100 * p[0] / WORLD.width) + "%"; b.style.top = (100 * p[1] / WORLD.height) + "%";
      b.dataset.id = s.id; b.dataset.region = s.region;
      b.setAttribute("aria-label", s.name + ", " + KIND[s.kind] + (s.embed ? ", plays here" : ", opens operator site"));
      b.innerHTML = (t
        ? '<img src="' + esc(t) + '" alt="" width="64" height="64" loading="lazy">'
        : '<span class="ph">' + esc((KIND[s.kind] || "Cam").slice(0, 3)) + "</span>") +
        '<span class="mk-tip">' + esc(s.name) + "</span>";
      b.addEventListener("click", function () { location.hash = "#/observe/" + s.id; });
      layer.appendChild(b);
    });
    REG.sites.forEach(function (s) {
      var p = project(s.lon, s.lat), b = document.createElement("button");
      b.type = "button"; b.className = "mk site st-" + s.status.split(" ")[0]; b.dataset.site = s.id;
      b.style.left = (100 * p[0] / WORLD.width) + "%"; b.style.top = (100 * p[1] / WORLD.height) + "%";
      b.setAttribute("aria-label", "Ocean compute site: " + s.name + " (" + s.status + ")");
      b.innerHTML = '<span class="mk-tip">' + esc(s.name) + "</span>";
      b.addEventListener("click", function () { location.hash = "#/observe/" + s.id; });
      layer.appendChild(b);
    });
    var tog = $("#obs-sites-toggle");
    if (tog && !tog._bound) {
      tog._bound = true;
      tog.addEventListener("change", function (e) { $("#obs-map").classList.toggle("hide-sites", !e.target.checked); });
    }
  }
  function zoomTo(region) {
    var wrap = $("#obs-map");
    if (!wrap || !WORLD) return;
    if (region === "all") { wrap.style.setProperty("--z", 1); wrap.style.setProperty("--tx", "0%"); wrap.style.setProperty("--ty", "0%"); return; }
    var pts = REG.streams.filter(function (s) { return s.region === region; }).map(function (s) { return project(s.lon, s.lat); });
    if (!pts.length) return;
    var xs = pts.map(function (p) { return p[0]; }), ys = pts.map(function (p) { return p[1]; });
    var cx = (Math.min.apply(null, xs) + Math.max.apply(null, xs)) / 2, cy = (Math.min.apply(null, ys) + Math.max.apply(null, ys)) / 2;
    var span = Math.max(Math.max.apply(null, xs) - Math.min.apply(null, xs), (Math.max.apply(null, ys) - Math.min.apply(null, ys)) * 2, 60);
    var z = Math.max(1, Math.min(5, WORLD.width / (span * 2.2)));
    wrap.style.setProperty("--z", z);
    wrap.style.setProperty("--tx", (50 - 100 * cx / WORLD.width) + "%"); wrap.style.setProperty("--ty", (50 - 100 * cy / WORLD.height) + "%");
  }
  function drawRegions() {
    var box = $("#obs-regions"), counts = {};
    REG.streams.forEach(function (s) { counts[s.region] = (counts[s.region] || 0) + 1; });
    var html = '<button type="button" class="chip on" data-region="all" aria-pressed="true">All cameras <span>' + REG.streams.length + "</span></button>";
    REG.regions.forEach(function (r) {
      if (!counts[r.id]) return;
      html += '<button type="button" class="chip" data-region="' + r.id + '" aria-pressed="false">' + esc(r.label) + " <span>" + counts[r.id] + "</span></button>";
    });
    box.innerHTML = html;
    if (!box._bound) {
      box._bound = true;
      box.addEventListener("click", function (e) {
        var b = e.target.closest("[data-region]"); if (!b) return;
        ST.region = b.dataset.region;
        $$(".chip", box).forEach(function (c) { var on = c === b; c.classList.toggle("on", on); c.setAttribute("aria-pressed", on); });
        $$("#obs-markers .mk[data-region]").forEach(function (m) { m.classList.toggle("dim", ST.region !== "all" && m.dataset.region !== ST.region); });
        zoomTo(ST.region); drawGallery();
      });
    }
  }
  function thumbUrl(s) {
    if (s.provider && s.provider.video_id) return "https://i.ytimg.com/vi/" + s.provider.video_id + "/mqdefault.jpg";
    return null;
  }
  function regionLabel(id) {
    var r = REG.regions.filter(function (x) { return x.id === id; })[0];
    return r ? r.label : id;
  }
  function drawGallery() {
    var box = $("#obs-gallery"), count = $("#obs-gal-count");
    if (!box) return;
    var streams = REG.streams.filter(function (s) { return ST.region === "all" || s.region === ST.region; });
    /* Prefer playable cams first so the filmstrip leads with real pictures */
    streams = streams.slice().sort(function (a, b) {
      var sa = (a.embed && a.provider && a.provider.video_id) ? 0 : 1;
      var sb = (b.embed && b.provider && b.provider.video_id) ? 0 : 1;
      return sa - sb || a.name.localeCompare(b.name);
    });
    if (count) count.textContent = streams.length + (ST.region === "all" ? " worldwide — scroll" : " in " + regionLabel(ST.region));
    if (!streams.length) {
      var gap = REG.regions.filter(function (r) { return r.id === ST.region; })[0];
      box.innerHTML = '<p class="obs-gallery-empty">' + esc((gap && gap.gap) || "No cameras in this region yet.") +
        ' <a href="https://github.com/ejri/aquatic-guardian/issues/new?title=Stream%20suggestion" rel="noopener">Suggest one</a></p>';
      return;
    }
    box.innerHTML = streams.map(function (s) {
      var t = thumbUrl(s), off = /^(offline|removed|ended)$/.test(s.status || "");
      var live = !off && s.embed && s.provider && s.provider.type === "youtube_video";
      var thumb = t
        ? '<img src="' + esc(t) + '" alt="" width="320" height="180" loading="lazy">'
        : '<span class="ph">' + esc(KIND[s.kind] || "Camera") + "</span>";
      return '<button type="button" class="cam-card' + (ST.stream && ST.stream.id === s.id ? " on" : "") +
        '" data-id="' + esc(s.id) + '" aria-pressed="' + (ST.stream && ST.stream.id === s.id ? "true" : "false") + '">' +
        '<span class="thumb">' + thumb + (live ? '<span class="live-dot"><i></i>Live</span>' : "") + "</span>" +
        '<span class="meta"><b>' + esc(s.name) + "</b><span>" + esc(regionLabel(s.region)) + " · " + esc(KIND[s.kind] || "") +
        (off ? " · offline" : "") + "</span></span></button>";
    }).join("");
    if (!box._bound) {
      box._bound = true;
      box.addEventListener("click", function (e) {
        var c = e.target.closest(".cam-card"); if (!c) return;
        location.hash = "#/observe/" + c.dataset.id;
      });
    }
    /* Keep the selected camera card in view */
    var on = box.querySelector(".cam-card.on");
    if (on && on.scrollIntoView) try { on.scrollIntoView({ inline: "center", block: "nearest", behavior: U.reduced ? "auto" : "smooth" }); } catch (e) {}
  }
  function bindResearch() {
    var side = $(".obs-side");
    if (!side || side._resBound) return;
    side._resBound = true;
    side.addEventListener("click", function (e) {
      var det = e.target.closest("[data-detect]"); if (det) { startDetect(); return; }
      var c = e.target.closest("[data-goto]"); if (!c) return;
      activateTab(c.getAttribute("data-goto"));
      try { $("#obs-tabs").scrollIntoView({ behavior: U.reduced ? "auto" : "smooth", block: "start" }); } catch (err) {}
    });
  }
  function deadlineBanner() {
    var now = Date.now(), b = $("#obs-deadline");
    var s = REG.sites.filter(function (x) { return x.deadline && Date.parse(x.deadline.date) > now; })[0];
    if (!s) { b.hidden = true; return; }
    var hrs = (Date.parse(s.deadline.date) - now) / 3600e3;
    b.hidden = false;
    b.innerHTML = "<b>" + (hrs < 72 ? "Closing soon. " : "") + "</b>" + esc(s.deadline.text) + ' <a href="' + esc(s.deadline.url) + '" rel="noopener">Read the Federal Register notice</a> or <a href="#/observe/' + s.id + '">model the site</a>.';
  }

  /* ---------------------------------------------------------- select */
  function select(id) {
    var s = byId(id); if (!s) return;
    stopVision();
    ST.stream = s; ST.site = null; ST.ocean = null;
    $$("#obs-markers .mk").forEach(function (m) { m.classList.toggle("sel", m.dataset.id === id); });
    $("#obs-station").hidden = false;
    var kick = $("#obs-place-kicker");
    if (kick) kick.textContent = regionLabel(s.region);
    $("#obs-name").textContent = s.name;
    $("#obs-meta").innerHTML = esc(s.operator) + ". " + esc(KIND[s.kind]) + (s.depth_m != null ? ", about " + fmt(s.depth_m, 0) + " m deep" : "") +
      ". " + esc(s.ecosystem) + "." + (s.schedule ? " " + esc(s.schedule) + "." : "") + (s.note ? " " + esc(s.note) : "") +
      (s.verify ? ' <span class="pill warn">not yet verified live</span>' : "") +
      (s.status === "offline" ? ' <span class="pill warn">offline</span>' : "") +
      (s.status === "seasonal" ? ' <span class="pill">seasonal</span>' : "") +
      (s.kind === "aquarium" ? ' <span class="pill">aquarium, not open water</span>' : "");
    $("#obs-species").textContent = s.species.length ? "Often seen: " + s.species.join(", ") + "." : "";
    var mini = $("#obs-heat-mini"); if (mini) { mini.hidden = true; mini.textContent = ""; }
    mountPlayer(s);
    drawGallery();
    loadOcean(s);
    scenarioDefaults(s);
    animalsTab(s); rulesTab(s.lat, s.lon);
    $("#obs-vis-out").hidden = true;
    if (ST.scrolled) {
      try { $("#obs-station").scrollIntoView({ behavior: U.reduced ? "auto" : "smooth", block: "start" }); } catch (e) {}
    }
    ST.scrolled = true;
  }
  function openSite(id) {
    var s = site(id); if (!s) return;
    ST.site = s;
    var nearest = REG.streams.slice().sort(function (a, b) { return dist(a, s) - dist(b, s); })[0];
    if (!ST.stream) select(nearest.id);
    $("#obs-site-note").hidden = false;
    $("#obs-site-note").innerHTML = "<b>" + esc(s.name) + "</b> (" + esc(s.operator) + "; " + esc(s.status) + "). " + esc(s.summary) +
      (s.coords_note ? " " + esc(s.coords_note) : "") + (s.verify ? ' <span class="pill warn">figures need verification</span>' : "") +
      " Modelled below at the site's coordinates with live conditions there.";
    loadOcean({ lat: s.lat, lon: s.lon, id: s.id, sal_psu: 32 }, true);
    Object.keys(s.preset || {}).forEach(function (k) { var el = $("#sc-" + k.replace(/_/g, "-")); if (el) { el.value = s.preset[k]; if (el.type === "range") el.dispatchEvent(new Event("input")); } });
    rulesTab(s.lat, s.lon);
    activateTab("obs-tab-heat");
    $("#obs-tabs").scrollIntoView({ behavior: U.reduced ? "auto" : "smooth", block: "start" });
    runScenario();
  }
  function dist(a, b) { return Math.hypot(a.lat - b.lat, (a.lon - b.lon) * Math.cos(a.lat * Math.PI / 180)); }

  /* ---------------------------------------------------------- player */
  function loadYT() {
    if (ST.ytReady) return ST.ytReady;
    ST.ytReady = new Promise(function (res, rej) {
      if (window.YT && window.YT.Player) return res(window.YT);
      var prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () { if (prev) prev(); res(window.YT); };
      var s = document.createElement("script"); s.src = "https://www.youtube.com/iframe_api"; s.onerror = function () { rej(new Error("YouTube player did not load. A content blocker may be stopping it.")); };
      document.head.appendChild(s);
    });
    return ST.ytReady;
  }
  function loadHlsLib() {
    if (window.Hls) return Promise.resolve(window.Hls);
    return new Promise(function (res, rej) {
      var s = document.createElement("script"); s.src = HLS_CDN; s.async = true;
      s.onload = function () { res(window.Hls); };
      s.onerror = function () { rej(new Error("hls.js failed to load")); };
      document.head.appendChild(s);
    });
  }
  function tearDownPlayer() {
    stopVision();
    if (ST.hls) { try { ST.hls.destroy(); } catch (e) {} ST.hls = null; }
    if (ST.player && ST.player.destroy) { try { ST.player.destroy(); } catch (e) {} }
    ST.player = null; ST.video = null;
  }
  function playerShell() {
    var box = $("#obs-player");
    box.innerHTML = '<div id="obs-media" class="obs-media"></div><canvas id="vis-overlay" class="vis-overlay" aria-hidden="true"></canvas>';
    return { media: $("#obs-media"), overlay: $("#vis-overlay") };
  }
  function mountPlayer(s) {
    var credit = $("#obs-credit");
    tearDownPlayer();
    var shell = playerShell(), media = shell.media;
    var url = s.provider.url || "#";
    var explore = s.provider.explore_url;
    var link = '<a href="' + esc(url) + '" rel="noopener" target="_blank">' + esc(url.replace(/^https?:\/\//, "").replace(/\/$/, "")) + "</a>";
    var exploreLink = explore ? ' · <a href="' + esc(explore) + '" rel="noopener" target="_blank">explore.org</a>' : "";
    var canYt = s.provider.type === "youtube_video" && s.provider.video_id && s.embed !== false;
    if (canYt) {
      credit.innerHTML = esc(s.operator) + ". Source: " + link + exploreLink + ".";
      media.innerHTML = '<p class="obs-loading">Loading stream…</p>';
      tryHls(s).then(function (ok) {
        if (!ST.stream || ST.stream.id !== s.id) return;
        if (!ok) mountYtIframe(s, media, credit, link, exploreLink);
      });
    } else {
      media.innerHTML = facadeHtml(s, null);
      credit.innerHTML = "Source: " + link + ".";
    }
  }
  function tryHls(s) {
    var vid = s.provider.video_id;
    var playlist = "/api/yt/hls?v=" + encodeURIComponent(vid);
    return fetch("/api/yt/status").then(function (r) { return r.ok ? r.json() : { yt_dlp: false }; }).catch(function () { return { yt_dlp: false }; })
      .then(function (st) {
        if (!st.yt_dlp) return false;
        return fetch(playlist, { method: "GET" }).then(function (r) {
          if (!r.ok) return false;
          return r.text().then(function (body) {
            if (!body || body.indexOf("#EXTM3U") !== 0) return false;
            return attachHlsVideo(s, playlist);
          });
        }).catch(function () { return false; });
      });
  }
  function attachHlsVideo(s, playlist) {
    var media = $("#obs-media"); if (!media) return false;
    media.innerHTML = "";
    var v = document.createElement("video");
    v.id = "obs-video"; v.className = "obs-video"; v.muted = true; v.playsInline = true; v.autoplay = true; v.controls = true;
    v.setAttribute("playsinline", ""); v.setAttribute("aria-label", s.name + " live stream");
    media.appendChild(v);
    ST.video = v;
    function ready() {
      if (!ST.stream || ST.stream.id !== s.id) return false;
      var msg = $("#vis-msg");
      if (msg) msg.textContent = "Stream ready. Press Find animals to look for animals in this video.";
      return true;
    }
    if (v.canPlayType("application/vnd.apple.mpegurl")) {
      v.src = playlist;
      return v.play().then(function () { return ready(); }).catch(function () { return ready(); });
    }
    return loadHlsLib().then(function (Hls) {
      if (!Hls || !Hls.isSupported()) return false;
      var h = new Hls({ enableWorker: true, lowLatencyMode: true });
      ST.hls = h;
      h.loadSource(playlist);
      h.attachMedia(v);
      return new Promise(function (res) {
        h.on(Hls.Events.MANIFEST_PARSED, function () {
          v.play().then(function () { res(ready()); }).catch(function () { res(ready()); });
        });
        h.on(Hls.Events.ERROR, function (_e, data) {
          if (data && data.fatal) { try { h.destroy(); } catch (err) {} ST.hls = null; res(false); }
        });
      });
    }).catch(function () { return false; });
  }
  function mountYtIframe(s, media, credit, link, exploreLink) {
    media.innerHTML = '<div id="obs-yt"></div>';
    credit.innerHTML = "Live from " + esc(s.name) + (s.operator ? " (" + esc(s.operator) + ")" : "") + ". To find animals, your browser will ask to share this tab. Source: " + link + exploreLink + ".";
    var msg = $("#vis-msg");
    if (msg) msg.textContent = "Your browser will ask to share this tab so the detector can see the video. Choose This tab.";
    loadYT().then(function (YT) {
      if (!ST.stream || ST.stream.id !== s.id) return;
      ST.player = new YT.Player("obs-yt", { host: "https://www.youtube-nocookie.com", videoId: s.provider.video_id,
        playerVars: { autoplay: 1, mute: 1, playsinline: 1, rel: 0, modestbranding: 1 },
        events: { onError: function (e) {
          var why = { 2: "invalid video id", 5: "HTML5 player error", 100: "stream ended or removed", 101: "embedding blocked", 150: "embedding blocked" }[e.data] || ("error " + e.data);
          media.innerHTML = facadeHtml(s, why);
        } } });
    }).catch(function (e) { media.innerHTML = facadeHtml(s, e.message); });
  }
  function facadeHtml(s, why) {
    var thumb = s.provider.video_id
      ? '<img class="facade-thumb" src="https://i.ytimg.com/vi/' + esc(s.provider.video_id) + '/hqdefault.jpg" alt="" width="480" height="360" loading="lazy">'
      : "";
    var reason = why
      ? "<p><b>Cannot play here:</b> " + esc(why) + ".</p><p>Open the operator link, or use a video file for detection.</p>"
      : (s.operator && /Ocean Networks Canada/i.test(s.operator)
        ? "<p><b>" + esc(s.name) + "</b> is on ONC's scheduled player (not embeddable).</p><p>" + esc(s.schedule || "See ONC Live Cameras.") + "</p><p>Open their page, or use a video file.</p>"
        : "<p class=\"f-k\">" + esc(KIND[s.kind] || s.kind) + "</p><p><b>" + esc(s.name) + "</b> uses " + esc(s.operator) + "'s player (not embeddable" +
          (s.note && /licen/i.test(s.note) ? " without a licence" : "") + ").</p><p>Open it, or use a video file for detection.</p>");
    return '<div class="facade">' + thumb + reason +
      '<a class="btn glow sm" href="' + esc(s.provider.url) + '" rel="noopener" target="_blank">Open live view</a></div>';
  }

  /* ----------------------------------------------------------- ocean */
  function loadOcean(s, forSite) {
    var box = $("#obs-ocean"), strip = $("#obs-now");
    box.innerHTML = '<p class="muted">Fetching live conditions for ' + fmt(s.lat, 2) + ", " + fmt(s.lon, 2) + "…</p>"; strip.innerHTML = "";
    OD.oceanNow(s).then(function (o) {
      if (!forSite && ST.stream && ST.stream.id !== s.id) return;
      ST.ocean = o; ST.oceanFor = s;
      renderNow(o); renderOcean(o, s); scenarioFromOcean(o, s); animalsTab(ST.stream);
    });
  }
  function renderNow(o) {
    var m = o.marine || {}, r = o.reef || {};
    // Prefer CRW 5 km for SST / anomaly / DHW so the three temperature tiles share one source.
    var sst = r.sst_c != null ? fmt(r.sst_c, 1) + " °C" : (m.sst_c != null ? fmt(m.sst_c, 1) + " °C" : "n/a");
    var anom = r.anomaly_c != null ? (r.anomaly_c >= 0 ? "+" : "") + fmt(r.anomaly_c, 1) + " °C" : "n/a";
    var dhwVal = r.dhw, dhw = dhwVal != null ? fmt(dhwVal, 1) + " °C-weeks" : "n/a";
    var alert = r.baa_label ? " · " + r.baa_label : (dhwVal != null && dhwVal >= 4 ? " · bleaching likely from 4" : "");
    var cur = m.current_ms != null ? fmt(m.current_ms, 2) + " m/s" : "n/a";
    var tide = m.tide_range_m != null ? fmt(m.tide_range_m, 2) + " m" : "n/a";
    $("#obs-now").innerHTML =
      '<div class="tiles" role="group" aria-label="Temperature">' +
        '<p class="tiles__h">Temperature</p>' +
        '<div class="tile"><b class="tile__value">' + sst + '</b><span class="tile__label">Sea surface' + (r.sst_c != null ? " (CRW 5 km)" : " (model)") + '</span></div>' +
        '<div class="tile"><b class="tile__value">' + anom + '</b><span class="tile__label">vs long-term average for this date (CRW anomaly)</span></div>' +
        '<div class="tile"><b class="tile__value">' + dhw + '</b><span class="tile__label">Coral heat stress (CRW DHW)' + alert + '</span></div>' +
      "</div>" +
      '<div class="tiles tiles--movement" role="group" aria-label="Water movement">' +
        '<p class="tiles__h">Water movement</p>' +
        '<div class="tile" data-field="current_ms"><b class="tile__value">' + cur + '</b><span class="tile__label">Surface current (model)</span></div>' +
        '<div class="tile" data-field="tide_range_m"><b class="tile__value">' + tide + '</b><span class="tile__label">Tide range, next 3 days</span></div>' +
      "</div>";
  }
  function renderOcean(o, s) {
    var m = o.marine, m90 = o.marine90, r = o.reef, rs = o.reefSeries, t = o.tide, html = "";
    if (r) html += '<div class="baa b' + r.baa + '"><b>' + esc(r.baa_label) + "</b> on NOAA Coral Reef Watch's 7-day bleaching alert scale; " + fmt(r.dhw, 1) +
      " degree heating weeks (4 means bleaching is likely in corals, 8 widespread bleaching and death). Satellite pixel " + fmt(r.lat, 3) + ", " + fmt(r.lon, 3) + ", " + esc(String(r.date).slice(0, 10)) + ".</div>";
    if (m && m.current_dir != null) {
      html += '<div class="obs-cur-arrow"><div class="needle" aria-hidden="true"><span style="transform:rotate(' + (+m.current_dir) + 'deg)"></span></div>' +
        "<div>Surface current now: <b>" + fmt(m.current_ms, 2) + " m/s</b> toward <b>" + fmt(m.current_dir, 0) + "°</b> (oceanographic direction, Open-Meteo).</div></div>";
    }
    html += '<div class="obs-ocean-grid ocean-grid">';
    html += '<figure><svg id="obs-sst-svg" viewBox="0 0 640 220" role="img" aria-label="Sea surface temperature over about 90 days"></svg><figcaption>Sea surface temperature (~90 days). Dashed line is MMM+1 °C bleaching threshold when Coral Reef Watch anomaly is available (SST − anomaly + 1).</figcaption></figure>';
    html += '<figure><svg id="obs-dhw-svg" viewBox="0 0 640 220" role="img" aria-label="Degree heating weeks over about 12 weeks"></svg><figcaption>Degree heating weeks (Coral Reef Watch). Alert bands at 4 (bleaching likely) and 8 (widespread bleaching and mortality).</figcaption></figure>';
    html += '<figure><svg id="obs-tide-svg" viewBox="0 0 640 220" role="img" aria-label="Sea level over three days"></svg><figcaption>Sea level including tide, from ' + esc(t ? t.source : "Open-Meteo Marine") + ". The line marks now.</figcaption></figure>";
    html += '<figure><svg id="obs-cur-svg" viewBox="0 0 640 220" role="img" aria-label="Current speed over three days"></svg><figcaption>Surface current speed, Open-Meteo Marine (MeteoFrance/Copernicus model, about 8 km grid). The peak sets the tidal-cycle run in the data-centre tab.</figcaption></figure>';
    html += "</div><ul class=\"srcs\">";
    if (m) html += "<li>Open-Meteo Marine grid cell " + fmt(m.grid_lat, 3) + ", " + fmt(m.grid_lon, 3) + "; local time " + esc(m.time || "") + " (" + esc(m.timezone || "") + ").</li>";
    Object.keys(o.errors).forEach(function (k) {
      var lab = { marine: "Model ocean data", marine90: "90-day SST model", reef: "Coral Reef Watch", reefSeries: "Coral Reef Watch time series", tide: "Tide station" }[k] || k;
      html += "<li class=\"err\">" + esc(lab) + " unavailable: " + esc(o.errors[k]) + (k === "tide" ? "" : ". Set a relay (see README) if your browser blocks this source.") + "</li>";
    });
    html += "</ul>";
    $("#obs-ocean").innerHTML = html;
    var nowT = Date.now();
    /* SST 90-day: prefer CRW daily; fall back to Open-Meteo hourly downsampled daily */
    (function () {
      var svg = $("#obs-sst-svg"); if (!svg) return;
      var pts = [], mmm1 = null, spanD = 90, nowD = spanD;
      if (rs && rs.time && rs.time.length) {
        var t0 = Date.parse(rs.time[0]) / 864e5;
        pts = rs.time.map(function (tm, i) { return [Date.parse(tm) / 864e5 - t0, rs.sst[i]]; }).filter(function (p) { return p[1] != null; });
        spanD = Math.max(1, pts.length ? pts[pts.length - 1][0] : 90);
        nowD = nowT / 864e5 - t0;
        var lastA = null, lastS = null;
        for (var i = rs.anomaly.length - 1; i >= 0; i--) { if (rs.anomaly[i] != null && rs.sst[i] != null) { lastA = rs.anomaly[i]; lastS = rs.sst[i]; break; } }
        if (lastA != null) mmm1 = lastS - lastA + 1;
      } else if (m90 && m90.hourly && m90.hourly.time.length) {
        var ht0 = Date.parse(m90.hourly.time[0]) / 864e5;
        var daily = {};
        m90.hourly.time.forEach(function (tm, i) {
          var v = m90.hourly.sst[i]; if (v == null) return;
          var day = Math.floor(Date.parse(tm) / 864e5 - ht0);
          if (daily[day] == null) daily[day] = { s: 0, n: 0 };
          daily[day].s += v; daily[day].n += 1;
        });
        pts = Object.keys(daily).map(Number).sort(function (a, b) { return a - b; }).map(function (d) { return [d, daily[d].s / daily[d].n]; });
        spanD = pts.length ? pts[pts.length - 1][0] : 90;
        nowD = nowT / 864e5 - ht0;
        if (r && r.sst_c != null && r.anomaly_c != null) mmm1 = r.sst_c - r.anomaly_c + 1;
      }
      plotSeries(svg, pts, spanD, nowD, "Days from start", "SST (°C)", "#9ED8E6", mmm1 != null ? [{ y: mmm1, color: "#FF9470", dash: "6 4", label: "MMM+1 °C" }] : []);
    })();
    /* DHW ~12 weeks from CRW series */
    (function () {
      var svg = $("#obs-dhw-svg"); if (!svg || !rs || !rs.time) return;
      var start = Math.max(0, rs.time.length - 84);
      var t0 = Date.parse(rs.time[start]) / 864e5;
      var pts = [];
      for (var i = start; i < rs.time.length; i++) {
        if (rs.dhw[i] == null) continue;
        pts.push([Date.parse(rs.time[i]) / 864e5 - t0, rs.dhw[i]]);
      }
      // Same floor as SST: a single CRW day leaves x-span 0 and U.chart would emit NaN/Infinity.
      var spanD = Math.max(1, pts.length ? pts[pts.length - 1][0] : 84), nowD = nowT / 864e5 - t0;
      plotSeries(svg, pts, spanD, nowD, "Days from start", "DHW (°C·weeks)", "#C9A3FF", [
        { y: 4, color: "#F7B24A", dash: "5 4", label: "DHW 4" },
        { y: 8, color: "#FF9470", dash: "5 4", label: "DHW 8" }
      ]);
    })();
    if (m && m.hourly.time.length) {
      var ts = m.hourly.time.map(function (x) { return Date.parse(x) / 3600e3; }), t0 = ts[0];
      var sl = t && t.predictions && t.predictions.length ? t.predictions.map(function (q) { return [Date.parse(q.t) / 3600e3 - t0, q.v]; }) : m.hourly.sea_level.map(function (v, i) { return [ts[i] - t0, v]; }).filter(function (p) { return p[1] != null; });
      var cu = m.hourly.current.map(function (v, i) { return [ts[i] - t0, v]; }).filter(function (p) { return p[1] != null; });
      var nowH = nowT / 3600e3 - t0, span = Math.max(1, ts[ts.length - 1] - t0);
      plotSeries($("#obs-tide-svg"), sl, span, nowH, "Hours from start", "Sea level (m)", "#9ED8E6");
      plotSeries($("#obs-cur-svg"), cu, span, nowH, "Hours from start", "Current (m/s)", "#F7B24A");
    }
  }
  function plotSeries(svg, pts, span, now, xl, yl, color, hlines) {
    if (!svg || !pts.length) return;
    pts = pts.filter(function (p) { return isFinite(p[0]) && isFinite(p[1]); });
    if (!pts.length) return;
    var ys = pts.map(function (p) { return p[1]; }), lo = Math.min.apply(null, ys), hi = Math.max.apply(null, ys);
    (hlines || []).forEach(function (h) { if (h && h.y != null && isFinite(h.y)) { lo = Math.min(lo, h.y); hi = Math.max(hi, h.y); } });
    var pad = (hi - lo) * 0.1 || 0.1;
    var xmax = Math.max(span, pts[pts.length - 1][0], 1e-6);
    var nowX = isFinite(now) ? now : xmax;
    U.chart(svg, { x: { min: 0, max: xmax, label: xl }, y: { min: lo - pad, max: hi + pad, label: yl },
      series: [{ pts: pts, color: color, width: 2.2 }], vlines: [{ x: nowX, color: "#DCEAEE", dash: "4 4", label: "now" }],
      hlines: hlines || [] });
  }

  /* ---------------------------------------------------------- vision */
  function bindVision() {
    var runBtn = $("#vis-run"); if (runBtn) runBtn.addEventListener("click", toggleDetect);
    var file = $("#vis-file"); if (file) file.addEventListener("change", function (e) { var f = e.target.files[0]; if (f) V.fromFile(f).then(function (src) { run(src, "file " + f.name, false); }, fail); });
    var model = $("#vis-model");
    if (model) model.addEventListener("change", function (e) {
      var f = e.target.files[0]; if (!f) return;
      $("#vis-model-status").textContent = "Loading detector…";
      V.OnnxDetector.load(f, +$("#vis-model-size").value, $("#vis-model-labels").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean))
        .then(function (d) { ST.detector = d; if (ST.engine) ST.engine.detector = d; $("#vis-model-status").textContent = f.name + " loaded."; },
          function (er) { $("#vis-model-status").textContent = er.message; });
    });
    var pick = $("#vis-model-pick");
    if (pick) pick.addEventListener("change", function () { loadBundledModel(pick.value); });
    var stop = $("#vis-stop"); if (stop) stop.addEventListener("click", stopVision);
    var how = $("#vis-how-sure-link");
    if (how) how.addEventListener("click", function (e) {
      e.preventDefault();
      var box = $("#vis-how-sure"); if (box) box.hidden = !box.hidden;
    });
    loadModelCatalog();
  }
  function liveVideo() {
    var v = ST.video || $("#obs-video");
    return v && v.tagName === "VIDEO" ? v : null;
  }
  function playerCropTarget() {
    return $("#obs-yt") || ($("#obs-media") && $("#obs-media").querySelector("iframe")) || $("#obs-video") || $("#obs-media") || $("#obs-player");
  }
  function videoPixelsReadable(v) {
    if (!v || v.readyState < 2 || !v.videoWidth) return false;
    try {
      var c = document.createElement("canvas"); c.width = 8; c.height = 8;
      var x = c.getContext("2d"); x.drawImage(v, 0, 0, 8, 8); x.getImageData(0, 0, 1, 1);
      return true;
    } catch (e) { return false; }
  }
  function toggleDetect() {
    if (ST.engine) { stopVision(false); $("#vis-msg").textContent = "Stopped."; return; }
    startDetect();
  }
  function startDetect() {
    var msg = $("#vis-msg");
    if (msg) msg.textContent = "Loading detector…";
    var v = liveVideo();
    if (v && videoPixelsReadable(v)) {
      V.fromVideo(v).then(function (src) { run(src, "live stream", true); }, fail);
      return;
    }
    if (v && v.readyState < 2) {
      V.fromVideo(v).then(function (src) { run(src, "live stream", true); }, function () { startCapture(playerCropTarget()); });
      return;
    }
    if (msg) msg.textContent = 'Choose "This tab" in the browser prompt.';
    startCapture(playerCropTarget());
  }
  function loadModelCatalog() {
    fetch("models/models.json").then(function (r) { return r.json(); }).then(function (cat) {
      ST.modelCatalog = cat;
      var pick = $("#vis-model-pick");
      if (pick) {
        pick.innerHTML = (cat.models || []).map(function (m) {
          return '<option value="' + esc(m.id) + '"' + (m.id === cat.default ? " selected" : "") + ">" + esc(m.label) + "</option>";
        }).join("");
      }
      var cand = $("#vis-model-candidates");
      if (cand && cat.candidates && cat.candidates.length) {
        cand.innerHTML = "<p class=\"small muted\">Also worth integrating next:</p><ul class=\"small\">" +
          cat.candidates.map(function (c) {
            return "<li><a href=\"" + esc(c.url) + "\" rel=\"noopener\" target=\"_blank\">" + esc(c.label) + "</a> — " + esc(c.note) + "</li>";
          }).join("") + "</ul>";
      }
      if (cat.default) loadBundledModel(cat.default);
    }).catch(function () {
      var st = $("#vis-model-status");
      if (st) st.textContent = "Bundled model catalogue missing; motion detection still works, or load an .onnx file.";
    });
  }
  function loadBundledModel(id) {
    var cat = ST.modelCatalog; if (!cat) return;
    var m = (cat.models || []).filter(function (x) { return x.id === id; })[0];
    var st = $("#vis-model-status");
    if (!m) return;
    if (!m.file) {
      ST.detector = null; ST.detectorConf = undefined;
      if (ST.engine) ST.engine.detector = null;
      if (st) st.textContent = "Using motion detection only.";
      return;
    }
    if (st) st.textContent = "Loading detector (first time only)…";
    if ($("#vis-model-size")) $("#vis-model-size").value = String(m.size || 320);
    if ($("#vis-model-labels")) $("#vis-model-labels").value = (m.labels || []).join(", ");
    ST.detectorConf = (m.conf != null) ? m.conf : undefined;
    V.OnnxDetector.load(m.file, m.size || 320, m.labels || [], { preprocess: m.preprocess, architecture: m.architecture })
      .then(function (d) {
        ST.detector = d;
        if (ST.engine) { ST.engine.detector = d; if (ST.detectorConf != null) ST.engine.o.conf = ST.detectorConf; }
        if (st) st.textContent = m.label + " ready. Labels map to 12 plain groups. " + (m.note || "");
      }, function (er) {
        ST.detector = null;
        if (ST.engine) ST.engine.detector = null;
        if (st) st.textContent = "Could not load " + m.label + " (" + er.message + "). Using motion until the ONNX is present.";
      });
  }
  function fail(e) {
    var msg = $("#vis-msg");
    if (!msg) return;
    if (e && e.name === "NotAllowedError") msg.textContent = "Sharing was cancelled. Press Find animals to try again.";
    else msg.textContent = "Detector failed to start. Try another browser, or use a video file.";
  }
  function setDetectUi(running) {
    var run = $("#vis-run"), stop = $("#vis-stop");
    if (run) { run.textContent = running ? "Stop" : "Find animals"; run.disabled = false; }
    if (stop) { stop.hidden = true; stop.disabled = true; }
  }
  function startCapture(el) {
    V.captureTab(el).then(function (src) {
      if (!src.cropped && el && !src.crop) src.crop = V.cropFromElement(src.video, el);
      var full = src.video.videoWidth * src.video.videoHeight, used = src.crop ? src.crop.w * src.crop.h : full;
      if (!src.cropped && full && used / full > 0.85 && el) {
        var retry = V.cropFromElement(src.video, $("#obs-player") || el);
        if (retry && retry.w * retry.h < used) src.crop = retry;
      }
      run(src, el ? "this camera" : "another tab", true);
    }, fail);
  }
  function run(src, label, boxesOnly) {
    stopVision(true);
    ST.history = [];
    ST.peakCount = 0;
    var overlay = $("#vis-overlay") || $("#vis-canvas");
    var eng = new V.Engine({ streamId: (ST.stream && ST.stream.id) || "file", fps: 5, conf: ST.detectorConf });
    eng.attach(src, overlay, { boxesOnly: !!boxesOnly });
    if (src.crop) eng.setCrop(src.crop);
    if (ST.detector) eng.detector = ST.detector;
    ST.engine = eng; ST.visSrc = src;
    setDetectUi(true);
    $("#vis-msg").textContent = "Looking for animals · up to 5 frames per second";
    var out = $("#obs-vis-out"); if (out) out.hidden = false;
    eng.start(showMetrics);
    if (src.stream) src.stream.getVideoTracks()[0].addEventListener("ended", function () { stopVision(false); });
  }
  function stopVision(keepVideo) {
    if (ST.engine) { ST.engine.stop(); ST.engine = null; }
    if (ST.ws) { ST.ws.close(); ST.ws = null; }
    var ov = $("#vis-overlay");
    if (ov) { var x = ov.getContext("2d"); if (x) x.clearRect(0, 0, ov.width, ov.height); }
    setDetectUi(false);
    if (!keepVideo) { /* tearDownPlayer clears video when changing streams */ }
  }
  function showMetrics(m) {
    if (m.error) { $("#vis-msg").textContent = m.error; return; }
    $("#obs-vis-out").hidden = false;
    var now = m.count || 0;
    if (now > (ST.peakCount || 0)) ST.peakCount = now;
    var groups = m.groups || {};
    var groupBits = Object.keys(groups).filter(function (k) { return groups[k] > 0; })
      .map(function (k) { return esc(k) + " " + groups[k]; });
    var cells = [
      ["Now", String(now)],
      ["Peak", String(ST.peakCount || 0)],
      ["Visibility", fmt(100 * (m.visibility || 0), 0) + "/100"]
    ];
    if (m.speed_bl_s != null) cells.push(["Speed", fmt(m.speed_bl_s, 2) + " body lengths/s"]);
    $("#vis-ro").innerHTML = cells.map(function (c) { return '<div class="ro"><b>' + c[1] + "</b><span>" + c[0] + "</span></div>"; }).join("") +
      (groupBits.length ? '<div class="ro"><b>' + groupBits.join(" · ") + "</b><span>By group</span></div>" : "");
    var fps = m.fps != null ? fmt(m.fps, 1) : null;
    $("#vis-msg").textContent = fps && fps < 1.5
      ? "Your device is slow, so we check about 1 frame per second."
      : ("Looking for animals · " + (fps || "5") + " frames per second");
    $("#vis-src").textContent = (m.source || "browser") + (fps ? ", " + fps + " fps" : "") + (m.detections != null ? ", " + m.detections + " boxes this frame" : "");
    var sum = $("#vis-summary");
    if (sum) {
      sum.textContent = now === 0
        ? "No animals seen in the last few seconds. Murky water or night can hide them."
        : ("Now " + now + " · peak " + (ST.peakCount || now) + (groupBits.length ? ", mostly " + groupBits[0].replace(/ \d+$/, "") : "") + ".");
    }
    var fl = m.flags || [];
    $("#vis-flags").innerHTML = fl.length ? fl.map(function (f) { return "<li>" + esc(f) + "</li>"; }).join("") :
      "<li>Counts are animals in view, not a population estimate.</li>";
    ST.history.push([Date.now(), now, 100 * (m.activity || 0)]);
    if (ST.history.length > 600) ST.history.shift();
    if (ST.history.length > 2 && ST.history.length % 3 === 0) {
      var t0 = ST.history[0][0];
      U.chart($("#vis-chart"), { x: { min: 0, max: Math.max(30, (ST.history[ST.history.length - 1][0] - t0) / 1000), label: "Seconds" },
        y: { min: 0, max: Math.max(5, Math.max.apply(null, ST.history.map(function (h) { return h[1]; })) + 1), label: "Animals in view" },
        series: [{ pts: ST.history.map(function (h) { return [(h[0] - t0) / 1000, h[1]]; }), color: "#F7B24A", width: 2 }] });
    }
  }

  /* -------------------------------------------------------- scenario */
  var SC_FIELDS = ["it-mw", "pue", "delta-t-k", "reuse", "n-ports", "port-depth", "spacing", "sst", "current", "salinity", "chronic"];
  function bindScenario() {
    SC_FIELDS.forEach(function (k) {
      var el = $("#sc-" + k); if (!el) return;
      var out = $("#sc-" + k + "-o");
      var upd = function () { if (out) out.textContent = el.value + (el.dataset.u ? " " + el.dataset.u : ""); };
      el.addEventListener("input", function () { upd(); debounceRun(); }); upd();
    });
    $("#sc-mode").addEventListener("change", debounceRun);
    $("#sc-rule").addEventListener("change", debounceRun);
    $("#sc-mc").addEventListener("click", monteCarlo);
    $("#sc-lab").addEventListener("click", function () { if (ST.lastScenario && U.plumesLoad) { U.plumesLoad(ST.lastScenario); location.hash = "#/lab/sim-plumes"; } });
    $("#sc-json").addEventListener("click", function () { if (!ST.lastScenario) return; download("scenario.json", JSON.stringify(ST.lastScenario, null, 2), "application/json"); });
  }
  var timer = null;
  function debounceRun() { clearTimeout(timer); timer = setTimeout(runScenario, 120); }
  function setVal(id, v) { var el = $("#sc-" + id); if (!el || v == null || isNaN(v)) return; el.value = v; el.dispatchEvent(new Event("input")); }
  function scenarioDefaults(s) {
    setVal("salinity", s.sal_psu || 33);
    setVal("port-depth", Math.max(8, Math.min(40, (s.depth_m && s.depth_m > 3 && s.depth_m < 60) ? Math.round(s.depth_m + 5) : 15)));
    var j = P.guessJurisdiction(s.lat, s.lon); $("#sc-rule").value = P.JUR_RULE[j] || "custom";
  }
  function scenarioFromOcean(o, s) {
    var m = o.marine || {}, r = o.reef || {};
    setVal("sst", Math.round(10 * (m.sst_c != null ? m.sst_c : (r.sst_c != null ? r.sst_c : 12))) / 10);
    setVal("current", Math.round(100 * Math.max(0.02, m.current_ms != null ? m.current_ms : 0.1)) / 100);
    runScenario();
  }
  function num(id) { return +$("#sc-" + id).value; }
  function buildScenario() {
    var loc = ST.site || ST.stream || { lat: 0, lon: 0 };
    var o = ST.ocean && ST.ocean.marine;
    var design = { it_mw: num("it-mw"), pue: num("pue"), delta_t_k: num("delta-t-k"), reuse_fraction: num("reuse") / 100, n_ports: num("n-ports"),
      spacing: num("spacing"), port_depth: num("port-depth"), mode: $("#sc-mode").value,
      // screening frame: x runs with the current and the ports discharge with it (PLUMES convention);
      // the compass bearing of the live current does not change a steady, uniform-current result
      horizontal_angle: 0 };
    void loc; void o;
    return P.buildDataCentre(design, { sst_c: num("sst"), salinity: num("salinity"), current_ms: num("current"), acute_m: Math.min(30, num("chronic") / 5), chronic_m: num("chronic") });
  }
  function runScenario() {
    if (!$("#sc-it-mw")) return;
    var sc, res, rule = $("#sc-rule").value, msg = $("#sc-msg");
    try {
      sc = buildScenario();
      res = P.run(sc, { rule: rule, custom_increment: null });
    } catch (e) { msg.textContent = "The model could not run with these inputs: " + e.message; return; }
    msg.textContent = "";
    ST.lastScenario = sc; ST.lastRun = res;
    var m = res.metrics, th = m.thermal, c = res.compliance, nf = m.nearfield;
    var v = $("#sc-verdict");
    v.className = "verdict " + (c.verdict === "within the limit" ? "ok" : c.verdict === "over the limit" ? "bad" : "na");
    v.innerHTML = "<b>" + esc(c.verdict[0].toUpperCase() + c.verdict.slice(1)) + "</b> — " + esc(c.rule.label) + " (" + esc(c.rule.source) + ")" +
      (c.rule.verify ? '. <span class="pill warn">' + esc(c.rule.verify_note || "verify") + "</span>" : "") +
      (rule === "custom" ? " Enter a limit above to compare, or leave as-is to report the rise only." : "");
    var reach05 = th.threshold_reach.filter(function (r) { return r.threshold_c === 0.5; })[0];
    var cells = [
      ["Heat to water", fmt(m.heat.heat_to_water_mw, 1) + " MW"], ["Cooling flow", fmt(m.heat.flow_m3s, 2) + " m³/s"],
      ["Near-field dilution", fmt(nf.dilution, 0) + "×"], ["Warmer at the mixing-zone edge", (th.dt_chronic_c != null ? fmt(th.dt_chronic_c, 2) : "n/a") + " °C"],
      ["Warmer than 0.5 °C for", reach05 && reach05.distance_m != null ? fmt(reach05.distance_m, 0) + " m" : "n/a"],
      ["Oxygen capacity lost at the pipe", fmt(m.oxygen.loss_end_of_pipe_mg_l, 2) + " mg/L"]
    ];
    $("#sc-ro").innerHTML = cells.map(function (q, i) { return '<div class="ro' + (i === 3 ? " hot" : "") + '"><b>' + q[1] + "</b><span>" + q[0] + "</span></div>"; }).join("");
    var ph = c.rule.status === "placeholder";
    var checks = c.checks.map(function (k) { return "<li><b>" + (k.pass === null ? "Not assessed" : ph ? (k.pass ? "Below" : "Above") : (k.pass ? "Pass" : "Exceeds")) + "</b><span>" + esc(k.check) + ": " + (k.value_c == null ? "n/a" : fmt(k.value_c, 3)) + " °C against " + (k.limit_c == null ? "n/a" : fmt(k.limit_c, 2)) + " °C" + (k.basis ? " (" + esc(k.basis) + ")" : "") + "</span></li>"; });
    $("#sc-checks").innerHTML = checks.join("") + res.caveats.map(function (q) { return "<li><b>Caveat</b><span>" + esc(q) + "</span></li>"; }).join("") +
      (m.merging ? "<li><b>Merging</b><span>Neighbouring plumes cost " + fmt(m.merging.penalty_pct, 1) + "% of the dilution a lone port would reach.</span></li>" : "") +
      "<li><b>Regime</b><span>" + esc(m.flow_class.regime) + "; port Froude number " + fmt(m.flow_class.port_froude, 1) + ".</span></li>";
    drawSide(res); drawDecay(res, c);
    tidal(sc, rule);
    updateHeatMini(c, th);
  }
  function updateHeatMini(c, th) {
    var mini = $("#obs-heat-mini"); if (!mini) return;
    var cls = c.verdict === "within the limit" ? "ok" : c.verdict === "over the limit" ? "bad" : "na";
    var edge = th.dt_chronic_c != null ? fmt(th.dt_chronic_c, 2) + " °C warmer" : "warming not available";
    mini.hidden = false;
    mini.className = "obs-heat-mini callout " + cls;
    mini.innerHTML =
      '<div class="callout__text">' +
        "<b>If a 24 MW seawater-cooled data centre were built here:</b> water at the edge of the mixing zone would be " + edge + "." +
        '<span class="callout__meta">' + esc(c.verdict[0].toUpperCase() + c.verdict.slice(1)) +
        (c.verdict === "no limit set for this location" ? ". Enter one to compare." : " · " + esc(c.rule.label)) + "</span>" +
      "</div>" +
      '<button type="button" class="btn line sm callout__action" data-goto="obs-tab-heat">See the full heat screen</button>';
  }
  function drawSide(res) {
    var st = res.nearfield.steps, svg = $("#sc-side"), last = st[st.length - 1];
    var xmax = Math.max(5, last.distance * 1.15, 1), zmax = res.nearfield.steps[0].depth + 2;
    var up = st.map(function (s) { return [s.distance, -(s.depth - s.diameter / 2)]; }), dn = st.map(function (s) { return [s.distance, -(s.depth + s.diameter / 2)]; }), cl = st.map(function (s) { return [s.distance, -s.depth]; });
    U.chart(svg, { x: { min: 0, max: xmax, label: "Distance from the outfall (m)" }, y: { min: -zmax, max: 0.5, label: "Height (m, 0 = surface)", fmt: function (v) { return fmt(v, 0); } },
      series: [{ pts: up, color: "#eb7958", width: 1.2, dash: "3 3" }, { pts: dn, color: "#eb7958", width: 1.2, dash: "3 3" }, { pts: cl, color: "#F7B24A", width: 2.4 }],
      hlines: [{ y: 0, color: "#9ED8E6", label: "surface" }] });
  }
  function drawDecay(res, c) {
    var pts = [], st = res.nearfield.steps, dT0 = res.metrics.thermal.dt_discharge_c, ff = res.farfield;
    st.forEach(function (s) { if (s.distance > 0.05) pts.push([s.distance, Math.abs(dT0) / s.dilution]); });
    if (ff) ff.rows.forEach(function (r) { pts.push([Math.max(r.distance, 0.06), Math.abs(r.delta_t)]); });
    if (!pts.length) return;
    var lim = c.checks[0] && c.checks[0].limit_c, mz = ST.lastScenario.mixing_zone;
    var ymin = 0.01, ymax = Math.max(Math.abs(dT0), 1) * 1.3;
    U.chart($("#sc-decay"), { x: { min: 0.1, max: Math.max(mz.chronic * 2, pts[pts.length - 1][0]), log: true, label: "Distance from the outfall (m)" },
      y: { min: ymin, max: ymax, log: true, label: "Warmer than ambient (°C)" },
      series: [{ pts: pts.filter(function (p) { return p[1] > ymin; }), color: "#F7B24A", width: 2.4 }],
      hlines: lim ? [{ y: lim, color: "#FF9470", dash: "6 4", label: "screening limit " + fmt(lim, 2) + " °C" }] : [],
      vlines: [{ x: mz.chronic, color: "#9ED8E6", dash: "4 4", label: "mixing zone" }] });
  }
  function tidal(sc, rule) {
    var peak = ST.ocean && ST.ocean.marine && ST.ocean.marine.current_peak_ms;
    var box = $("#sc-tide");
    if (!peak) { box.innerHTML = '<p class="muted">Tidal-cycle screening needs the live current forecast.</p>'; return; }
    var t = P.tidalCycle(sc, peak, { n: 24, rule: rule, custom_increment: null });
    box.innerHTML = '<div class="tidebar" role="img" aria-label="Pass or exceed at 24 points through a tidal cycle">' + t.rows.map(function (r) {
      return '<span class="' + (r.pass === false ? "bad" : r.pass ? "ok" : "na") + (r.slack ? " slack" : "") + '" title="hour ' + fmt(r.hour, 1) + ": " + fmt(r.u_ms, 2) + " m/s, " + fmt(r.dt_chronic_c, 2) + ' °C"></span>';
    }).join("") + "</div><p>Through one 12.4-hour tide with a peak current of " + fmt(peak, 2) + " m/s, the mixing-zone edge exceeds the limit for " +
      (t.fraction_of_cycle_exceeding == null ? "an unknown share" : fmt(100 * t.fraction_of_cycle_exceeding, 0) + "%") + " of the cycle; tidal excursion about " + fmt(t.excursion_km, 1) +
      " km. Slack-water bars are outlined: each bar is a steady run, so re-entrainment at slack is not represented and those bars understate warming.</p>";
  }
  function monteCarlo() {
    if (!ST.lastScenario) return;
    var base = ST.lastScenario, out = [], rng = mulberry(7), rule = $("#sc-rule").value;
    var R = { aspiration: [0.08, 0.12], forced_scale: [0.65, 1.0], alpha: [0.0001, 0.0005], current_factor: [0.5, 1.5], ambient_dt: [-1, 1] };
    $("#sc-mc-out").textContent = "Running 80 scenarios…";
    setTimeout(function () {
      for (var i = 0; i < 80; i++) {
        var s = JSON.parse(JSON.stringify(base)), d = {};
        Object.keys(R).forEach(function (k) { d[k] = R[k][0] + rng() * (R[k][1] - R[k][0]); });
        s.settings = Object.assign({}, s.settings, { aspiration: d.aspiration, forced_scale: d.forced_scale });
        s.ambient.rows.forEach(function (r) { r.alpha = d.alpha; r.speed *= d.current_factor; r.far_speed = Math.max(1e-4, r.far_speed * d.current_factor); r.temperature += d.ambient_dt; });
        try { out.push(P.run(s, { rule: rule, isolated_check: false, custom_increment: null }).metrics.thermal.dt_chronic_c); } catch (e) {}
      }
      out.sort(function (a, b) { return a - b; });
      var q = function (p) { return out[Math.min(out.length - 1, Math.round(p * (out.length - 1)))]; };
      $("#sc-mc-out").textContent = "Mixing-zone-edge warming across " + out.length + " runs: 5th percentile " + fmt(q(0.05), 3) + " °C, median " + fmt(q(0.5), 3) + " °C, 95th percentile " + fmt(q(0.95), 3) +
        " °C. Varied: aspiration 0.08–0.12, forced entrainment 0.65–1.0 (model form), Brooks alpha 1–5×10⁻⁴, current ±50%, water temperature ±1 °C.";
    }, 20);
  }
  function mulberry(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function download(name, text, type) { var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: type })); a.download = name; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
  U.download = U.download || download;

  /* --------------------------------------------------------- animals */
  var BANDS = [
    { match: /reef|coral/i, who: "Reef-building corals", tier: "Invertebrates (cnidarians); sentience not established", rule: "NOAA Coral Reef Watch: 4 °C-weeks of heat stress makes bleaching likely; 8 brings widespread bleaching and death.", dhw: true },
    { match: /kelp|pacific|salish|fjord|barkley|pinnacle|monterey/i, who: "Giant kelp", tier: "Algae", rule: "Stress commonly reported near or above 18–20 °C.", hi: 18, verify: true },
    { match: /salish|fjord|pacific rocky|discovery|douglas|north coast|barkley|campbell/i, who: "Pacific salmon", tier: "Vertebrate fishes, recognised as sentient (UK Animal Welfare (Sentience) Act 2022; NY Declaration 2024)", rule: "Washington marine 1-DMax criteria 13–16 °C for the highest-use waters; embryo harm above 17.5 °C; acute lethality for adults near 22–23 °C.", hi: 16 },
    { match: /seagrass|eelgrass|estuar|bay/i, who: "Eelgrass", tier: "Plants", rule: "Stress commonly reported near 25 °C.", hi: 25, verify: true },
    { match: /rocky|kelp|reef|pacific/i, who: "Decapod crustaceans (crabs, lobsters, shrimp)", tier: "Recognised as sentient under the UK Animal Welfare (Sentience) Act 2022 after the LSE review (Birch et al. 2021)", rule: "Early life stages (e.g. Dungeness crab larvae) are the most heat-sensitive; species thresholds need primary literature.", verify: true },
    { match: /reef|rocky|kelp|vent|canyon/i, who: "Cephalopods (octopus, squid)", tier: "Recognised as sentient under the same Act", rule: "No screening threshold transcribed; treat any sustained warming as needing species review.", verify: true }
  ];
  function animalsTab(s) {
    if (!s) return;
    var o = ST.ocean, sst = o && o.marine && o.marine.sst_c != null ? o.marine.sst_c : (o && o.reef ? o.reef.sst_c : null), dhw = o && o.reef ? o.reef.dhw : null;
    var dt = ST.lastRun && ST.lastRun.metrics.thermal.dt_chronic_c;
    var hay = s.ecosystem + " " + s.species.join(" ") + " " + s.region;
    var rows = BANDS.filter(function (b) { return b.match.test(hay); });
    if (!rows.length) rows = [BANDS[5]];
    $("#obs-animals").innerHTML = '<table class="bands"><thead><tr><th>Who lives here</th><th>Standing</th><th>Heat reference</th><th>Today</th></tr></thead><tbody>' + rows.map(function (b) {
      var today = "n/a";
      if (b.dhw && dhw != null) today = fmt(dhw, 1) + " °C-weeks" + (dhw >= 8 ? " (above 8)" : dhw >= 4 ? " (above 4)" : "");
      else if (b.hi && sst != null) { var margin = b.hi - sst; today = fmt(sst, 1) + " °C; " + (margin > 0 ? fmt(margin, 1) + " °C below the reference" : fmt(-margin, 1) + " °C above it") + (dt != null ? "; a data centre here would add about " + fmt(dt, 2) + " °C at the mixing-zone edge" : ""); }
      return "<tr><td><b>" + esc(b.who) + "</b></td><td>" + esc(b.tier) + "</td><td>" + esc(b.rule) + (b.verify ? ' <span class="pill warn">placeholder, needs species literature</span>' : "") + "</td><td>" + today + "</td></tr>";
    }).join("") + "</tbody></table><p class=\"muted\">The thermal safety margin, not plume size, is what a temperature increment spends in summer: the same 0.5 °C matters most when the water is already close to a species' limit.</p>";
  }

  /* ----------------------------------------------------------- rules */
  function rulesTab(lat, lon) {
    var j = P.guessJurisdiction(lat, lon), rid = P.JUR_RULE[j] || "custom", r = P.RULES[rid];
    var J = (window.AG_DATA && window.AG_DATA.jurisdictions || []).filter(function (x) { return x.id === j || (j === "us-ca-bay" && x.id === "us-ca"); })[0];
    var names = { "us-wa": "Washington", "us-ca": "California", "us-ca-bay": "California (San Francisco Bay)", "us-or": "Oregon", "us-other": "Other United States waters", "ca-bc": "British Columbia", eu: "European Union member state", other: "Not transcribed" };
    $("#obs-rules").innerHTML = "<p><b>" + esc(names[j]) + "</b>, guessed from the coordinates (" + fmt(lat, 2) + ", " + fmt(lon, 2) + "). Screening rule: <b>" + esc(r.label) + "</b>, " + esc(r.source) + "." +
      (r.verify ? ' <span class="pill warn">' + esc(r.verify_note || "verify") + "</span>" : "") + "</p>" + (J ? "<p>" + esc(J.note) + "</p>" : "") +
      '<p>Draft permit and bill language for this jurisdiction is in the <a href="#/officials">policy toolkit</a>.</p>' +
      '<h4>Ocean compute on the map</h4><ul class="sites">' + REG.sites.map(function (s) {
        return '<li><a href="#/observe/' + s.id + '"><b>' + esc(s.name) + "</b></a> <span>" + esc(s.status) + ". " + esc(s.summary) + "</span></li>";
      }).join("") + "</ul><p class=\"muted\">None of these projects has published ecological monitoring of its thermal plume.</p>";
  }

  /* ------------------------------------------------------------ tabs */
  function bindTabs() {
    var tl = $("#obs-tabs [role=tablist]");
    tl.addEventListener("click", function (e) { var t = e.target.closest("[role=tab]"); if (t) activateTab(t.id); });
    tl.addEventListener("keydown", function (e) {
      var tabs = $$("[role=tab]", tl), i = tabs.indexOf(document.activeElement);
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); var n = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length]; n.focus(); activateTab(n.id); }
    });
  }
  function activateTab(id) {
    $$("#obs-tabs [role=tab]").forEach(function (t) { var on = t.id === id; t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1; $("#" + t.getAttribute("aria-controls")).hidden = !on; });
    if (id === "obs-tab-heat" && !ST.lastRun) runScenario();
  }
  U.obs = { select: select, openSite: openSite, state: ST, project: project };
})();
