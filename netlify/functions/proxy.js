/**
 * Allow-listed CORS proxy for ocean-data sources that reject browser origins.
 * Mirrors relay/app.py PROXY_HOSTS so Live ocean works on Netlify without Fly.
 */
const ALLOWED = new Set([
  "marine-api.open-meteo.com",
  "coastwatch.pfeg.noaa.gov",
  "coastwatch.noaa.gov",
  "pae-paha.pacioos.hawaii.edu",
  "api.tidesandcurrents.noaa.gov",
  "api-iwls.dfo-mpo.gc.ca",
  "www.ndbc.noaa.gov",
  "data.oceannetworks.ca",
]);

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers: cors(), body: "" };
  }
  if (event.httpMethod !== "GET") {
    return { statusCode: 405, headers: cors(), body: "GET only" };
  }
  const raw = (event.queryStringParameters && event.queryStringParameters.url) || "";
  let u;
  try {
    u = new URL(raw);
  } catch {
    return json(400, { error: "Missing or invalid url parameter" });
  }
  if (u.protocol !== "https:" || !ALLOWED.has(u.hostname)) {
    return json(403, { error: "Host not on the allow-list: " + u.hostname });
  }
  try {
    const r = await fetch(u.toString(), {
      headers: { "User-Agent": "AquaticGuardianNetlifyProxy/1.0 (+https://github.com/ejri/aquatic-guardian)" },
    });
    const text = await r.text();
    if (!r.ok) {
      return json(502, { error: "Upstream " + u.hostname + " returned " + r.status, body: text.slice(0, 400) });
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { text };
    }
    return {
      statusCode: 200,
      headers: {
        ...cors(),
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=300",
      },
      body: JSON.stringify(data),
    };
  } catch (e) {
    return json(502, { error: String(e.message || e) });
  }
};

function cors() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function json(statusCode, obj) {
  return { statusCode, headers: { ...cors(), "Content-Type": "application/json" }, body: JSON.stringify(obj) };
}
