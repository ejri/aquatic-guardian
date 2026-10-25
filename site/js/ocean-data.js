/* ocean-data.js: live ocean conditions for any stream location.
 * Sources (all free, no key): Open-Meteo Marine (SST, currents, sea level incl.
 * tides; MeteoFrance/Copernicus 0.08 deg), NOAA Coral Reef Watch on CoastWatch
 * ERDDAP (degree heating weeks, SST anomaly, bleaching alert area), NOAA CO-OPS
 * (US tides and water temperature), DFO IWLS (Canadian tides).
 * Each call tries the browser first; if CORS blocks it and window.AG_RELAY is
 * set, it retries through the relay's allow-listed proxy.
 */
(function (root) {
  "use strict";
  var TTL_MIN = 20;
  function cacheGet(k) { try { var v = JSON.parse(sessionStorage.getItem("ag:" + k)); if (v && Date.now() - v.t < TTL_MIN * 60000) return v.d; } catch (e) {} return null; }
  function cacheSet(k, d) { try { sessionStorage.setItem("ag:" + k, JSON.stringify({ t: Date.now(), d: d })); } catch (e) {} }
  function timeoutFetch(url, ms) {
    var ctl = "AbortController" in root ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctl) ctl.abort(); }, ms || 12000);
    return fetch(url, ctl ? { signal: ctl.signal } : {}).then(function (r) {
      clearTimeout(timer);
      if (!r.ok) throw new Error("HTTP " + r.status + " from " + new URL(url).host);
      return r.json();
    }, function (e) { clearTimeout(timer); throw e; });
  }
  /* Prefer an explicit relay, then same-origin Netlify/local proxies. */
  function proxyCandidates(url) {
    var q = encodeURIComponent(url), out = [];
    if (root.AG_RELAY) out.push(root.AG_RELAY.replace(/\/$/, "") + "/api/proxy?url=" + q);
    out.push("/.netlify/functions/proxy?url=" + q);
    out.push("/api/proxy?url=" + q);
    return out;
  }
  function getJSON(url, key) {
    var hit = key && cacheGet(key); if (hit) return Promise.resolve(hit);
    function throughProxies(err, list) {
      if (!list.length) throw err;
      return timeoutFetch(list[0]).catch(function (e2) { return throughProxies(e2, list.slice(1)); });
    }
    return timeoutFetch(url).catch(function (e) {
      return throughProxies(e, proxyCandidates(url));
    }).then(function (d) { if (key) cacheSet(key, d); return d; });
  }
  function r3(x) { return Math.round(x * 1000) / 1000; }

  /* ---- Open-Meteo Marine ---- */
  function openMeteo(lat, lon) {
    var vars = "sea_surface_temperature,wave_height,ocean_current_velocity,ocean_current_direction,sea_level_height_msl";
    var url = "https://marine-api.open-meteo.com/v1/marine?latitude=" + r3(lat) + "&longitude=" + r3(lon) +
      "&current=" + vars + "&hourly=" + vars + "&past_days=1&forecast_days=2&timezone=auto&cell_selection=sea";
    return getJSON(url, "om:" + r3(lat) + "," + r3(lon)).then(function (d) {
      var cu = (d.current_units && d.current_units.ocean_current_velocity) || "km/h";
      var k = /km/.test(cu) ? 1 / 3.6 : (/kn/.test(cu) ? 0.514444 : 1);
      var h = d.hourly || {}, c = d.current || {};
      var cur = (h.ocean_current_velocity || []).map(function (v) { return v == null ? null : v * k; });
      var sl = h.sea_level_height_msl || [];
      var valid = sl.filter(function (v) { return v != null; });
      var uMax = Math.max.apply(null, cur.filter(function (v) { return v != null; }).concat([0]));
      return {
        source: "Open-Meteo Marine", time: c.time, timezone: d.timezone, grid_lat: d.latitude, grid_lon: d.longitude,
        sst_c: c.sea_surface_temperature, wave_m: c.wave_height,
        current_ms: c.ocean_current_velocity == null ? null : c.ocean_current_velocity * k, current_dir: c.ocean_current_direction,
        sea_level_m: c.sea_level_height_msl,
        hourly: { time: h.time || [], sea_level: sl, current: cur, current_dir: h.ocean_current_direction || [], sst: h.sea_surface_temperature || [] },
        tide_range_m: valid.length ? Math.max.apply(null, valid) - Math.min.apply(null, valid) : null,
        current_peak_ms: uMax
      };
    });
  }

  /* ---- NOAA Coral Reef Watch (5 km daily) via ERDDAP ----
   * Prefer PacIOOS dhw_5km: coastwatch.pfeg NOAA_DHW currently 302s to a broken
   * mirror. Same variable names (CRW_*). */
  var BAA = ["No stress", "Bleaching watch", "Bleaching warning", "Alert level 1", "Alert level 2", "Alert level 3", "Alert level 4", "Alert level 5"];
  var CRW_HOSTS = [
    "https://pae-paha.pacioos.hawaii.edu/erddap/griddap/dhw_5km.json?",
    "https://coastwatch.pfeg.noaa.gov/erddap/griddap/NOAA_DHW.json?"
  ];
  function crwOnce(lat, lon, host) {
    var q = function (v) { return v + "[(last)][(" + lat.toFixed(3) + ")][(" + lon.toFixed(3) + ")]"; };
    var url = host + ["CRW_DHW", "CRW_SST", "CRW_SSTANOMALY", "CRW_BAA_7D_MAX"].map(q).join(",");
    return getJSON(url, "crw:" + host.split("/")[2] + ":" + lat.toFixed(2) + "," + lon.toFixed(2)).then(function (d) {
      var t = d.table, row = t.rows[0], col = function (n) { return row[t.columnNames.indexOf(n)]; };
      if (col("CRW_SST") == null || isNaN(col("CRW_SST"))) throw new Error("land or ice pixel");
      return { source: "NOAA Coral Reef Watch 5 km", date: col("time"), lat: col("latitude"), lon: col("longitude"),
        sst_c: col("CRW_SST"), anomaly_c: col("CRW_SSTANOMALY"), dhw: col("CRW_DHW"), baa: col("CRW_BAA_7D_MAX"), baa_label: BAA[col("CRW_BAA_7D_MAX")] || "Unknown" };
    });
  }
  function coralReefWatch(lat, lon) {
    // coastal cameras often sit on a land-masked pixel; step outward to the nearest ocean pixel
    var offs = [[0, 0], [0.05, 0], [-0.05, 0], [0, 0.05], [0, -0.05], [0.1, 0.1], [-0.1, -0.1], [0.1, -0.1], [-0.1, 0.1], [0.2, 0], [0, 0.2], [-0.2, 0], [0, -0.2]];
    var hi = 0;
    function tryHost(err) {
      if (hi >= CRW_HOSTS.length) return Promise.reject(err || new Error("Coral Reef Watch hosts unavailable"));
      var host = CRW_HOSTS[hi++], i = 0;
      function next(e0) {
        if (i >= offs.length) return tryHost(e0 || new Error("no ocean pixel within 0.2 deg"));
        var o = offs[i++];
        return crwOnce(lat + o[0], lon + o[1], host).catch(function (e) {
          // land/ice: try next offset; hard network failure on this host: next host
          if (/Failed to fetch|NetworkError|Load failed|abort|HTTP 50|HTTP 404|Not Found|unknown dataset/i.test(e.message || "")) {
            if (/land or ice/i.test(e.message || "")) return next(e);
            return tryHost(e);
          }
          if (/land or ice/i.test(e.message || "")) return next(e);
          return next(e);
        });
      }
      return next(err);
    }
    return tryHost();
  }

  /* ---- NOAA CO-OPS ---- */
  function coops(station) {
    var base = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station=" + station + "&datum=MLLW&units=metric&time_zone=gmt&application=AquaticGuardian&format=json";
    var pred = getJSON(base + "&product=predictions&interval=h&range=48&begin_date=" + yyyymmdd(new Date(Date.now() - 6 * 3600e3)), "coops-p:" + station);
    var temp = getJSON(base + "&product=water_temperature&date=latest", "coops-t:" + station).catch(function () { return null; });
    return Promise.all([pred, temp]).then(function (a) {
      var p = (a[0] && a[0].predictions) || [];
      var wt = a[1] && a[1].data && a[1].data[0];
      return { source: "NOAA CO-OPS " + station, predictions: p.map(function (q) { return { t: q.t + "Z", v: +q.v }; }),
        water_temp_c: wt ? +wt.v : null, water_temp_time: wt ? wt.t : null };
    });
  }
  function yyyymmdd(d) { return d.getUTCFullYear() + String(d.getUTCMonth() + 1).padStart(2, "0") + String(d.getUTCDate()).padStart(2, "0") + " " + String(d.getUTCHours()).padStart(2, "0") + ":00"; }

  /* ---- DFO / CHS IWLS ---- */
  function iwls(code) {
    var api = "https://api-iwls.dfo-mpo.gc.ca/api/v1";
    return getJSON(api + "/stations?code=" + code, "iwls-s:" + code).then(function (st) {
      if (!st.length) throw new Error("IWLS station " + code + " not found");
      var from = new Date(Date.now() - 6 * 3600e3).toISOString().slice(0, 19) + "Z", to = new Date(Date.now() + 42 * 3600e3).toISOString().slice(0, 19) + "Z";
      return getJSON(api + "/stations/" + st[0].id + "/data?time-series-code=wlp&from=" + from + "&to=" + to + "&resolution=SIXTY_MINUTES", "iwls-d:" + code)
        .then(function (d) { return { source: "DFO IWLS " + st[0].officialName, predictions: d.map(function (q) { return { t: q.eventDate, v: q.value }; }) }; });
    });
  }

  /* ---- combined ---- */
  function oceanNow(stream) {
    var tasks = {
      marine: openMeteo(stream.lat, stream.lon),
      reef: coralReefWatch(stream.lat, stream.lon),
      tide: stream.coops ? coops(stream.coops) : (stream.iwls_code ? iwls(stream.iwls_code) : Promise.reject(new Error("no tide station")))
    };
    var keys = Object.keys(tasks);
    return Promise.all(keys.map(function (k) { return tasks[k].then(function (v) { return { ok: true, v: v }; }, function (e) { return { ok: false, e: e.message || String(e) }; }); }))
      .then(function (res) { var o = { errors: {} }; keys.forEach(function (k, i) { if (res[i].ok) o[k] = res[i].v; else o.errors[k] = res[i].e; }); return o; });
  }

  root.OceanData = { openMeteo: openMeteo, coralReefWatch: coralReefWatch, coops: coops, iwls: iwls, oceanNow: oceanNow, BAA: BAA };
})(typeof self !== "undefined" ? self : this);
