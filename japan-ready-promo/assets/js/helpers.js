/* Shared helpers for every scene: voice timings, seeded randomness, map renderers.
   Everything here is deterministic — no clocks, no Math.random, no network. */
(function () {
  const CAP = window.CAPTIONS;
  const GEO = window.GEO;
  const NS = "http://www.w3.org/2000/svg";
  const byId = {};
  CAP.lines.forEach((l) => (byId[l.id] = l));

  const clean = (w) => w.toLowerCase().replace(/[^a-z0-9']/g, "");
  /** Global time (s) of a voice line. */
  const line = (id) => byId[id];
  /** Global start/end of a word in a line, e.g. word("L02", "Japan"). */
  const word = (id, w, nth = 0) => {
    const hits = byId[id].words.filter((x) => clean(x.w) === clean(w));
    const h = hits[nth] || hits[0];
    if (!h) throw new Error(`word ${w} not in ${id}`);
    return h;
  };
  const rng = (seed) => () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

  const toFeature = (c) => ({ type: "Feature", id: c.id, properties: { n: c.n }, geometry: c.g });
  const feats = {
    land110: { type: "Feature", geometry: GEO.land110 },
    c110: GEO.countries110.map(toFeature),
    c50: GEO.countries50.map(toFeature),
    borders110: { type: "Feature", geometry: GEO.borders110 },
  };
  const cities = GEO.cities;
  const HIGHLIGHT = { "050": "bd", "392": "jp" };

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  /** Orthographic globe, re-projected on every render(state). */
  function globe(svg, opts) {
    const o = Object.assign({ cx: 960, cy: 520 }, opts);
    const proj = d3.geoOrthographic().clipAngle(90).precision(0.6);
    const path = d3.geoPath(proj);
    const defs = el("defs", {}, svg);
    defs.innerHTML =
      '<radialGradient id="' + o.id + '-ocean" cx="38%" cy="32%" r="75%"><stop offset="0" stop-color="#1c3358"/><stop offset="0.7" stop-color="#11203a"/><stop offset="1" stop-color="#0b1529"/></radialGradient>' +
      '<radialGradient id="' + o.id + '-glow" cx="50%" cy="50%" r="50%"><stop offset="0.82" stop-color="#2a9d8f" stop-opacity="0"/><stop offset="0.9" stop-color="#5fc4b8" stop-opacity="0.22"/><stop offset="1" stop-color="#5fc4b8" stop-opacity="0"/></radialGradient>';
    const glow = el("circle", { fill: `url(#${o.id}-glow)` }, svg);
    const sphere = el("path", { fill: `url(#${o.id}-ocean)` }, svg);
    const grat = el("path", { fill: "none", stroke: "#5fc4b8", "stroke-opacity": "0.09", "stroke-width": "1" }, svg);
    const gLand = el("g", {}, svg);
    const countryEls = feats.c110.map((f) => {
      const k = HIGHLIGHT[f.id];
      return { f, k, e: el("path", { fill: k === "bd" ? "#2a9d8f" : k === "jp" ? "#e63946" : "#22365a", stroke: "#3a5684", "stroke-width": "0.6" }, gLand) };
    });
    const arc = el("path", { fill: "none", stroke: "#f4a261", "stroke-width": "5", "stroke-linecap": "round", "stroke-dasharray": "2 12" }, svg);
    const graticule = d3.geoGraticule10();
    const interp = d3.geoInterpolate(cities.dhaka, cities.tokyo);
    function render(s) {
      proj.rotate([-s.lon, -s.lat]).scale(s.scale).translate([o.cx, o.cy]);
      glow.setAttribute("cx", o.cx);
      glow.setAttribute("cy", o.cy);
      glow.setAttribute("r", s.scale * 1.12);
      sphere.setAttribute("d", path({ type: "Sphere" }));
      grat.setAttribute("d", path(graticule));
      countryEls.forEach(({ f, k, e }) => {
        e.setAttribute("d", path(f) || "");
        if (k === "jp") e.setAttribute("fill-opacity", s.jp == null ? 1 : s.jp);
        if (k === "bd") e.setAttribute("fill-opacity", s.bd == null ? 1 : s.bd);
      });
      const n = Math.max(2, Math.round(64 * (s.arc || 0)));
      if ((s.arc || 0) > 0.001) {
        const pts = [];
        for (let i = 0; i <= n; i++) pts.push(interp(((s.arc || 0) * i) / n));
        arc.setAttribute("d", path({ type: "LineString", coordinates: pts }) || "");
      } else arc.setAttribute("d", "");
    }
    /** Screen position of [lon,lat] under the last render, or null when on the far side. */
    function at(lonlat) {
      const r = proj.rotate();
      const visible = d3.geoDistance(lonlat, [-r[0], -r[1]]) < Math.PI / 2 - 0.02;
      return visible ? proj(lonlat) : null;
    }
    return { render, at, proj };
  }

  /** Flat Mercator map drawn once; camera moves are SVG transforms (cheap, crisp). */
  function flatMap(svg, opts) {
    const o = Object.assign({ center: [118, 32], scale: 1400, detail: "c50" }, opts);
    const proj = d3.geoMercator().center(o.center).scale(o.scale).translate([960, 540]);
    const path = d3.geoPath(proj);
    const cam = el("g", {}, svg);
    el("rect", { x: -6000, y: -6000, width: 14000, height: 14000, fill: "#0e1a30" }, cam);
    const grat = el("path", { d: path(d3.geoGraticule().step([5, 5])()), fill: "none", stroke: "#5fc4b8", "stroke-opacity": "0.07", "stroke-width": "1", "vector-effect": "non-scaling-stroke" }, cam);
    const land = el("g", {}, cam);
    const byKey = {};
    feats[o.detail].forEach((f) => {
      const k = HIGHLIGHT[f.id];
      const e = el("path", { d: path(f) || "", fill: k === "bd" ? "#2a9d8f" : k === "jp" ? "#e63946" : "#1f3254", stroke: "#3a5684", "stroke-width": "0.8", "vector-effect": "non-scaling-stroke" }, land);
      if (k) byKey[k] = e;
    });
    const top = el("g", {}, cam); // arcs etc. live in map space
    const overlay = el("g", {}, svg); // pins/labels stay screen-sized
    const camera = { x: 960, y: 540, z: 1 };
    function apply() {
      cam.setAttribute("transform", `translate(960 540) scale(${camera.z}) translate(${-camera.x} ${-camera.y})`);
    }
    function toScreen(p) {
      return [960 + (p[0] - camera.x) * camera.z, 540 + (p[1] - camera.y) * camera.z];
    }
    function lookAt(lonlat, z) {
      const p = proj(lonlat);
      return { x: p[0], y: p[1], z };
    }
    apply();
    return { proj, path, cam, top, overlay, camera, apply, toScreen, lookAt, byKey };
  }

  window.JS = { line, word, rng, feats, cities, globe, flatMap, el, NS };
})();
