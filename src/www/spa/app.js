"use strict";

const TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const TILE_ATTRIB = "© OpenStreetMap contributors";

const API_BASE = "https://api.10ulabs.com/wan-synthesizer";

const DEFAULT_MAP_ID = "daf";

const PROVIDER_KIND = "provider region";
const PROVIDER_STYLE = { color: "#ef6c00", radius: 5 };
const ROLE_STYLE = {
  wan_pop: { color: "#6a1b9a", radius: 8 },
  tenant: { color: "#1565c0", radius: 4 },
};

const LINK_STYLE = {
  homing: { color: ROLE_STYLE.tenant.color, weight: 1.5 },
  backbone: { color: ROLE_STYLE.wan_pop.color, weight: 4.5 },
};

const VIEW_CENTER = [39.5, -98.35];

const WAN_POP = "WAN PoP";

const LEGEND_ROWS = [
  { swatch: "dot", color: ROLE_STYLE.wan_pop.color, label: WAN_POP },
  { swatch: "dot", color: PROVIDER_STYLE.color, label: "Provider region" },
  { swatch: "dot", color: ROLE_STYLE.tenant.color, label: "Location", tenant: true },
  { swatch: "line", color: LINK_STYLE.backbone.color, label: "Fiber" },
  { swatch: "line", color: LINK_STYLE.homing.color, label: "Homing circuit" },
];

const map = L.map("map").setView(VIEW_CENTER, 4);
L.tileLayer(TILE_URL, { attribution: TILE_ATTRIB, maxZoom: 19 }).addTo(map);

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

function linkLabel(source, target) {
  return `<strong>${displayName(source)}</strong> ↔ <strong>${displayName(target)}</strong>`;
}

function segmentKey(left, right) {
  return [left, right].sort().join(" ↔ ");
}

function circuitsBySegment(circuits) {
  const crossing = new Map();
  for (const circuit of circuits) {
    const route = circuit.path || [];
    for (let step = 0; step + 1 < route.length; step += 1) {
      const key = segmentKey(route[step], route[step + 1]);
      crossing.set(key, (crossing.get(key) || []).concat([circuit]));
    }
  }
  return crossing;
}

function circuitLabel(circuit) {
  const ends = `${cityOf(circuit.source_name)} ↔ ${cityOf(circuit.target_name)}`;
  return `<strong>Circuit ${ends}</strong><br>${(circuit.path || []).join(" → ")}`;
}

function fiberLabel(source, target, circuits) {
  const fiber = `Fiber ${source.name} ↔ ${target.name}`;
  if (!circuits.length) {
    return fiber;
  }
  return [fiber, ...circuits.map(circuitLabel)].join("<br>");
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

function drawLinks(links, byId, style, label) {
  for (const link of links) {
    const source = byId[link.source_id];
    const target = byId[link.target_id];
    if (source && target) {
      add(L.polyline([displayCoords(source), displayCoords(target)], {
        color: style.color,
        weight: style.weight,
        opacity: 0.8,
      }).bindTooltip(label(source, target), { sticky: true }));
    }
  }
}

async function getJSON(path) {
  const response = await fetch(path);
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
  let links;
  let circuits;
  try {
    [sites, links, circuits] = await Promise.all([
      getJSON(`${API_BASE}/tenants/${tenantId}/sites`),
      getJSON(`${API_BASE}/tenants/${tenantId}/paths`),
      getJSON(`${API_BASE}/tenants/${tenantId}/backbone-links`),
    ]);
  } catch (error) {
    document.getElementById("counts").textContent = "WAN not synthesized yet";
    return;
  }
  showCounts(sites);

  const byId = indexById(sites);
  const physical = links.filter((link) => link.link_kind === "carrier_physical");
  const homings = links.filter(
    (link) => link.link_kind === "tenant_to_backbone" || link.link_kind === "provider_to_backbone",
  );
  const crossing = circuitsBySegment(circuits);
  drawLinks(physical, byId, LINK_STYLE.backbone, (source, target) =>
    fiberLabel(source, target, crossing.get(segmentKey(source.name, target.name)) || []));
  drawLinks(homings, byId, LINK_STYLE.homing, linkLabel);
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

async function init() {
  const nav = document.getElementById("tenants");
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

init().catch((error) => {
  console.error(error);
});
