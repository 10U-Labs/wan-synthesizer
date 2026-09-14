"use strict";

const COUNTRY_STYLE = { color: "#aab4be", weight: 0.7, fillColor: "#f4f4f1", fillOpacity: 1 };
const COUNTRIES_ATTRIB = "Made with Natural Earth";
const WORLD_COPIES = [-360, 0, 360];

const API_BASE = "https://api.10ulabs.com";

const GOOGLE_CLIENT_ID = "846587722064-qjou8en4tk96n12ii3rgnpjshnbqovok.apps.googleusercontent.com";
const HOSTED_DOMAIN = "10ulabs.com";
const ID_TOKEN_KEY = "wan-synthesizer-id-token";
const INACTIVITY_LIMIT_MINUTES = 15;
const ACTIVITY_EVENTS = ["pointerdown", "pointermove", "keydown", "wheel"];

const SIGN_IN_NOTES = {
  first: `Sign in with a ${HOSTED_DOMAIN} account.`,
  401: "Your sign-in has expired. Sign in again.",
  403: `That account is not authorized for the WAN Synthesizer. Sign in with one that is.`,
  expired: "Your sign-in has expired. Sign in again.",
  idle: `You were signed out after ${INACTIVITY_LIMIT_MINUTES} minutes without activity. Sign in again.`,
  out: "You signed out.",
};

const DEFAULT_MAP_ID = "daf";

const ROLE_STYLE = {
  wan_pop: { color: "#6a1b9a", radius: 8 },
  tenant: { color: "#1565c0", radius: 4 },
  provider: { color: "#ef6c00", radius: 5 },
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
  { swatch: "dot", color: ROLE_STYLE.provider.color, label: "Provider region" },
  { swatch: "dot", color: ROLE_STYLE.tenant.color, label: "Site", tenant: true },
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
    tenantLegendText.textContent = `${label} Site`;
  }
}

function styleFor(site) {
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
  const region = site.country === "United States" ? site.state : site.country;
  const located = site.municipality && region
    ? `<br>${site.municipality}, ${region}`
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
      const key = segmentKey(cityOf(route[step]), cityOf(route[step + 1]));
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
  return [site.latitude, nearLon(site.longitude)];
}

const HOMED_ROLE = {
  tenant_to_backbone: "tenant",
  provider_to_backbone: "provider",
};

function dotKey(tierRole, id) {
  return `${tierRole}:${id}`;
}

function indexByKey(dots) {
  const byKey = {};
  for (const dot of dots) {
    byKey[dotKey(dot.tier_role, dot.id)] = dot;
  }
  return byKey;
}

function vertices(rows, tierRole) {
  return rows.map((row) => ({ ...row, tier_role: tierRole }));
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

function drawFiber(segments, crossing) {
  for (const segment of segments) {
    const ends = [
      [segment.a_latitude, nearLon(segment.a_longitude)],
      [segment.z_latitude, nearLon(segment.z_longitude)],
    ];
    const key = segmentKey(segment.a_municipality, segment.z_municipality);
    add(L.polyline(ends, {
      color: LINE_STYLE.fiber.color,
      weight: LINE_STYLE.fiber.weight,
      opacity: 0.8,
    }).bindTooltip(circuitsLabel(crossing.get(key) || []), { sticky: true }));
  }
}

function drawHomings(homings, byKey) {
  for (const homing of homings) {
    const source = byKey[dotKey(HOMED_ROLE[homing.homing_kind], homing.source_id)];
    const target = byKey[dotKey("wan_pop", homing.target)];
    if (source && target) {
      add(L.polyline([displayCoords(source), displayCoords(target)], {
        color: LINE_STYLE.homing.color,
        weight: LINE_STYLE.homing.weight,
        opacity: 0.8,
      }).bindTooltip(homingLabel(source, target), { sticky: true }));
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

let expiryTimer = null;
let idleTimer = null;

function tokenExpiry(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return Number.isFinite(payload.exp) ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

function stopWatching() {
  clearTimeout(expiryTimer);
  clearTimeout(idleTimer);
}

function touch() {
  if (idToken === null) {
    return;
  }
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => endSession(SIGN_IN_NOTES.idle), INACTIVITY_LIMIT_MINUTES * 60 * 1000);
}

function watchSession() {
  stopWatching();
  const expiry = tokenExpiry(idToken);
  if (expiry === null) {
    endSession(SIGN_IN_NOTES[401]);
    return;
  }
  expiryTimer = setTimeout(() => endSession(SIGN_IN_NOTES.expired), Math.max(0, expiry - Date.now()));
  touch();
}

function openSession() {
  watchSession();
  if (idToken === null) {
    return Promise.resolve();
  }
  showApp();
  return start();
}

function onSignedIn(response) {
  idToken = response.credential;
  storeToken(idToken);
  openSession().catch((error) => {
    console.error(error);
  });
}

function endSession(note) {
  if (idToken === null) {
    return;
  }
  idToken = null;
  storeToken(null);
  stopWatching();
  showSignIn(note);
}

function turnedAway(status) {
  endSession(SIGN_IN_NOTES[status]);
}

function signOut() {
  google.accounts.id.disableAutoSelect();
  endSession(SIGN_IN_NOTES.out);
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
    if (tally[site.tier_role] !== undefined) {
      tally[site.tier_role] += 1;
    }
  }
  counts.textContent =
    `WAN PoPs ${tally.wan_pop}`
    + ` SITES ${tally.tenant}`
    + ` PROVIDER REGIONS ${tally.provider}`;
}

async function render(entry) {
  clear();
  let wanPops;
  let sites;
  let regions;
  let fiber;
  let homings;
  let circuits;
  try {
    [wanPops, sites, regions, fiber, homings, circuits] = await Promise.all([
      getJSON(`${API_BASE}/wan-syntheses/${entry.synthesis}/wan-pops`),
      getJSON(`${API_BASE}/wan-syntheses/${entry.synthesis}/sites`),
      getJSON(
        `${API_BASE}/wan-syntheses/${entry.synthesis}/hyperscale-cloud-service-provider-regions`,
      ),
      getJSON(`${API_BASE}/wan-syntheses/${entry.synthesis}/fiber-segments`),
      getJSON(`${API_BASE}/wan-syntheses/${entry.synthesis}/homing-circuits`),
      getJSON(`${API_BASE}/wan-synthesizer/tenants/${entry.tenant}/backbone-circuits`),
    ]);
  } catch (error) {
    document.getElementById("counts").textContent = "WAN not synthesized yet";
    return;
  }
  const dots = [
    ...vertices(wanPops, "wan_pop"),
    ...vertices(sites, "tenant"),
    ...vertices(regions, "provider"),
  ];
  showCounts(dots);

  drawFiber(fiber, circuitsBySegment(circuits));
  drawHomings(homings, indexByKey(dots));
  const points = drawSites(dots);

  if (points.length) {
    map.fitBounds(points, { padding: [30, 30] });
  }
}

function select(link, entry) {
  for (const other of document.querySelectorAll("#tenants a")) {
    other.classList.toggle("active", other === link);
  }
  showLegendTenant(link.textContent);
  return render(entry);
}

function slug(label) {
  return label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

async function start() {
  const nav = document.getElementById("tenants");
  nav.replaceChildren();
  const syntheses = await getJSON(`${API_BASE}/wan-syntheses`);
  const entries = syntheses.map(({ id, label }) => {
    const entry = { synthesis: id, tenant: slug(label) };
    const link = document.createElement("a");
    link.href = "#";
    link.textContent = label;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      select(link, entry);
    });
    nav.appendChild(link);
    return { link, entry };
  });
  const start = entries.find(({ entry }) => entry.tenant === DEFAULT_MAP_ID) || entries[0];
  if (start) {
    await select(start.link, start.entry);
  }
}

function init() {
  document.getElementById("sign-out").addEventListener("click", signOut);
  for (const type of ACTIVITY_EVENTS) {
    document.addEventListener(type, touch, { passive: true });
  }
  if (idToken) {
    return openSession();
  }
  showSignIn(SIGN_IN_NOTES.first);
  return Promise.resolve();
}

init().catch((error) => {
  console.error(error);
});
