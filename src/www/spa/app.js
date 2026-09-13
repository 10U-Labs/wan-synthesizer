"use strict";

const COUNTRY_STYLE = { color: "#aab4be", weight: 0.7, fillColor: "#f4f4f1", fillOpacity: 1 };
const COUNTRIES_ATTRIB = "Made with Natural Earth";
const WORLD_COPIES = [-360, 0, 360];

const API_BASE = "https://api.10ulabs.com/wan-synthesizer";

const GOOGLE_CLIENT_ID = "846587722064-qjou8en4tk96n12ii3rgnpjshnbqovok.apps.googleusercontent.com";
const HOSTED_DOMAIN = "10ulabs.com";
const ID_TOKEN_KEY = "wan-synthesizer-id-token";

const SIGN_IN_NOTES = {
  first: `Sign in with a ${HOSTED_DOMAIN} account.`,
  401: "Your sign-in has expired. Sign in again.",
  403: `That account is not authorized for the WAN Synthesizer. Sign in with one that is.`,
};

const DEFAULT_MAP_ID = "daf";

const PROVIDER_KIND = "provider region";
const PROVIDER_STYLE = { color: "#ef6c00", radius: 5 };
const ROLE_STYLE = {
  wan_pop: { color: "#6a1b9a", radius: 8 },
  tenant: { color: "#1565c0", radius: 4 },
};

const LINE_STYLE = {
  homing: { color: ROLE_STYLE.tenant.color, weight: 1.5 },
  fiber: { color: ROLE_STYLE.wan_pop.color, weight: 4.5 },
};

const VIEW_CENTER = [39.5, -98.35];

const WAN_POP = "WAN PoP";

const HOMING_CIRCUIT = "Homing circuit";

const LEGEND_ROWS = [
  { swatch: "dot", color: ROLE_STYLE.wan_pop.color, label: WAN_POP },
  { swatch: "dot", color: PROVIDER_STYLE.color, label: "Provider region" },
  { swatch: "dot", color: ROLE_STYLE.tenant.color, label: "Location", tenant: true },
  { swatch: "line", color: LINE_STYLE.fiber.color, label: "Fiber" },
  { swatch: "line", color: LINE_STYLE.homing.color, label: HOMING_CIRCUIT },
];

const map = L.map("map", { minZoom: 2, maxZoom: 12 }).setView(VIEW_CENTER, 4);
for (const shift of WORLD_COPIES) {
  L.geoJSON(NE_110M_ADMIN_0_COUNTRIES, {
    style: COUNTRY_STYLE,
    interactive: false,
    coordsToLatLng: ([lon, lat]) => L.latLng(lat, lon + shift),
  }).addTo(map);
}
map.attributionControl.addAttribution(COUNTRIES_ATTRIB);

let drawn = [];

let tenantLegendText = null;

const legend = L.control({ position: "bottomright" });

legend.onAdd = function onAdd() {
  const box = L.DomUtil.create("div", "legend");
  for (const row of LEGEND_ROWS) {
    const item = L.DomUtil.create("div", "legend-item", box);
    const swatch = L.DomUtil.create("span", `legend-swatch legend-${row.swatch}`, item);
    swatch.style.background = row.color;
    const text = L.DomUtil.create("span", "legend-label", item);
    text.textContent = row.label;
    if (row.tenant) {
      tenantLegendText = text;
    }
  }
  L.DomEvent.disableClickPropagation(box);
  return box;
};

legend.addTo(map);

function showLegendTenant(label) {
  if (tenantLegendText) {
    tenantLegendText.textContent = `${label} Location`;
  }
}

function styleFor(site) {
  if (site.kind === PROVIDER_KIND) {
    return PROVIDER_STYLE;
  }
  return ROLE_STYLE[site.tier_role] || null;
}

const TIER_PREFIX = {
  wan_pop: WAN_POP,
};

function cityOf(name) {
  return name.replace(/,\s*[^,]+$/, "");
}

function cityName(site) {
  return cityOf(site.name);
}

function displayName(site) {
  const prefix = TIER_PREFIX[site.tier_role];
  return prefix ? `${prefix} ${cityName(site)}` : site.name;
}

function siteLabel(site) {
  const info = site.info || {};
  const region = info.country === "United States" ? info.state : info.country;
  const located = info.municipality && region
    ? `<br>${info.municipality}, ${region}`
    : "";
  return `<strong>${displayName(site)}</strong>${located}`;
}

function homingLabel(source, target) {
  const ends = `${displayName(source)} ↔ ${displayName(target)}`;
  return `<strong>${HOMING_CIRCUIT} ${ends}</strong>`;
}

function segmentKey(left, right) {
  return [left, right].sort().join(" ↔ ");
}

function circuitsBySegment(circuits) {
  const crossing = new Map();
  for (const circuit of circuits) {
    const route = circuit.route || [];
    for (let step = 0; step + 1 < route.length; step += 1) {
      const key = segmentKey(route[step], route[step + 1]);
      crossing.set(key, (crossing.get(key) || []).concat([circuit]));
    }
  }
  return crossing;
}

function circuitLabel(circuit) {
  const ends = `${cityOf(circuit.source_name)} ↔ ${cityOf(circuit.target_name)}`;
  return `<strong>Circuit ${ends}</strong>`;
}

function circuitsLabel(circuits) {
  return circuits.map(circuitLabel).join("<br>");
}

function clear() {
  for (const layer of drawn) {
    map.removeLayer(layer);
  }
  drawn = [];
}

function add(layer) {
  layer.addTo(map);
  drawn.push(layer);
}

function siteMarker(site, coords) {
  const style = styleFor(site);
  if (!style) {
    return null;
  }
  return L.circleMarker(coords, {
    radius: style.radius,
    color: style.color,
    fillColor: style.color,
    fillOpacity: 0.85,
    weight: 1,
  }).bindTooltip(siteLabel(site));
}

function nearLon(lon) {
  let shifted = lon;
  while (shifted - VIEW_CENTER[1] > 180) {
    shifted -= 360;
  }
  while (shifted - VIEW_CENTER[1] < -180) {
    shifted += 360;
  }
  return shifted;
}

function displayCoords(site) {
  return [site.coords[0], nearLon(site.coords[1])];
}

function indexById(sites) {
  const byId = {};
  for (const site of sites) {
    byId[site.id] = site;
  }
  return byId;
}

function drawSites(sites) {
  const coords = [];
  for (const site of sites) {
    const at = displayCoords(site);
    const marker = siteMarker(site, at);
    if (marker) {
      add(marker);
      coords.push(at);
    }
  }
  return coords;
}

function drawLines(lines, byId, style, label) {
  for (const line of lines) {
    const source = byId[line.source_id];
    const target = byId[line.target_id];
    if (source && target) {
      add(L.polyline([displayCoords(source), displayCoords(target)], {
        color: style.color,
        weight: style.weight,
        opacity: 0.8,
      }).bindTooltip(label(source, target), { sticky: true }));
    }
  }
}

function storedToken() {
  try {
    return sessionStorage.getItem(ID_TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeToken(token) {
  try {
    if (token) {
      sessionStorage.setItem(ID_TOKEN_KEY, token);
    } else {
      sessionStorage.removeItem(ID_TOKEN_KEY);
    }
  } catch {
    return;
  }
}

let idToken = storedToken();

function showApp() {
  document.getElementById("sign-in").hidden = true;
  document.getElementById("app").hidden = false;
  map.invalidateSize();
}

function showSignIn(note) {
  document.getElementById("app").hidden = true;
  document.getElementById("sign-in-note").textContent = note;
  document.getElementById("sign-in").hidden = false;
  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    hd: HOSTED_DOMAIN,
    auto_select: true,
    callback: onSignedIn,
  });
  const button = document.getElementById("google-button");
  button.replaceChildren();
  google.accounts.id.renderButton(button, {
    theme: "outline",
    size: "large",
    text: "signin_with",
    shape: "pill",
    width: 300,
  });
}

function onSignedIn(response) {
  idToken = response.credential;
  storeToken(idToken);
  showApp();
  start().catch((error) => {
    console.error(error);
  });
}

function turnedAway(status) {
  if (idToken === null) {
    return;
  }
  idToken = null;
  storeToken(null);
  showSignIn(SIGN_IN_NOTES[status]);
}

async function getJSON(path) {
  const response = await fetch(path, {
    headers: { Authorization: `Bearer ${idToken}` },
  });
  if (response.status === 401 || response.status === 403) {
    turnedAway(response.status);
  }
  if (!response.ok) {
    throw new Error(`${path} → ${response.status}`);
  }
  return response.json();
}

function showCounts(sites) {
  const counts = document.getElementById("counts");
  const tally = { wan_pop: 0, tenant: 0, provider: 0 };
  for (const site of sites) {
    if (site.included !== false && tally[site.tier_role] !== undefined) {
      tally[site.tier_role] += 1;
    }
  }
  counts.textContent =
    `WAN PoPs ${tally.wan_pop}`
    + ` LOCATIONS ${tally.tenant}`
    + ` PROVIDER REGIONS ${tally.provider}`;
}

async function render(tenantId) {
  clear();
  let sites;
  let fiber;
  let homings;
  let circuits;
  try {
    [sites, fiber, homings, circuits] = await Promise.all([
      getJSON(`${API_BASE}/tenants/${tenantId}/sites`),
      getJSON(`${API_BASE}/tenants/${tenantId}/fiber-segments`),
      getJSON(`${API_BASE}/tenants/${tenantId}/homing-circuits`),
      getJSON(`${API_BASE}/tenants/${tenantId}/backbone-circuits`),
    ]);
  } catch (error) {
    document.getElementById("counts").textContent = "WAN not synthesized yet";
    return;
  }
  showCounts(sites);

  const byId = indexById(sites);
  const crossing = circuitsBySegment(circuits);
  drawLines(fiber, byId, LINE_STYLE.fiber, (source, target) =>
    circuitsLabel(crossing.get(segmentKey(source.name, target.name)) || []));
  drawLines(homings, byId, LINE_STYLE.homing, homingLabel);
  const points = drawSites(sites);

  if (points.length) {
    map.fitBounds(points, { padding: [30, 30] });
  }
}

function select(link, mapId) {
  for (const other of document.querySelectorAll("#tenants a")) {
    other.classList.toggle("active", other === link);
  }
  showLegendTenant(link.textContent);
  return render(mapId);
}

async function start() {
  const nav = document.getElementById("tenants");
  nav.replaceChildren();
  const tenants = await getJSON(`${API_BASE}/tenants`);
  const entries = tenants.map(({ id, label }) => {
    const link = document.createElement("a");
    link.href = "#";
    link.textContent = label;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      select(link, id);
    });
    nav.appendChild(link);
    return { link, id };
  });
  const start = entries.find((entry) => entry.id === DEFAULT_MAP_ID) || entries[0];
  if (start) {
    await select(start.link, start.id);
  }
}

function init() {
  if (idToken) {
    showApp();
    return start();
  }
  showSignIn(SIGN_IN_NOTES.first);
  return Promise.resolve();
}

init().catch((error) => {
  console.error(error);
});
