import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const template = await readFile(new URL("../templates/maps.html", import.meta.url), "utf8");
const moduleScript = template.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(moduleScript, "map page has its module script");

assert.match(template, /\/static\/map_selection\.js/);
assert.match(moduleScript, /const selection = createMapSelection\(\{\s*panels, Popup, document, unit: activeScale\.unit,\s*sample: useInterpolatedNoaa \? sampleGrid : undefined,/);
assert.match(moduleScript, /panel\.map\.on\("click", event => selection\.select\(event\.lngLat\)\)/);
assert.doesNotMatch(moduleScript.match(/panel\.map\.on\("click"[\s\S]*?\n\s*\}\);/)?.[0] || "", /fetch\(/,
    "click handling only updates the selected location; it does not request data");

const beginLoading = moduleScript.slice(moduleScript.indexOf("function startViewportLoad"), moduleScript.indexOf("function invalidateViewport"));
const invalidate = moduleScript.slice(moduleScript.indexOf("function invalidateViewport"), moduleScript.indexOf("panels.forEach((panel) => {", moduleScript.indexOf("function invalidateViewport")));
assert.match(beginLoading, /selection\.beginLoading\(panel\)/);
assert.match(beginLoading, /loadData\(panel, panel\.viewportGeneration\)/);
assert.match(invalidate, /selection\.beginLoading\(panel\)/,
    "viewport invalidation displays loading immediately, before the debounce fires");
assert.match(moduleScript, /panel\.moveTimer = setTimeout\(\(\) => startViewportLoad\(panel\), 350\)/,
    "viewport fetch remains debounced");

const staleGuard = /controller\.signal\.aborted\s*\|\|\s*generation !== panel\.viewportGeneration/;
assert.match(moduleScript, staleGuard, "stale successful responses are ignored");
assert.match(moduleScript, /generation === panel\.viewportGeneration[\s\S]*?selection\.fail\(panel\)/,
    "stale failures are ignored while current failures update the readout");
assert.match(moduleScript, /finally\s*\{[\s\S]*?panel\.requestController === controller/,
    "an older request cannot clear a newer request controller");

assert.match(moduleScript, /selection\.removePanel\(panel\)/);
assert.match(moduleScript, /clearTimeout\(panel\.moveTimer\)/);
assert.match(moduleScript, /panel\.requestController\?\.abort\(\)/);
assert.match(moduleScript, /generation|viewportGeneration/);
assert.match(moduleScript, /saveScale\(family, scale\)/);
assert.doesNotMatch(moduleScript, /selection\.[\s\S]{0,100}setPaintProperty/,
    "selection lifecycle does not mutate the shared map scale");

// Execute the template's real async viewport functions with deferred fake fetches.
const functionsSource = moduleScript.slice(
    moduleScript.indexOf("async function loadData"),
    moduleScript.indexOf("panels.forEach((panel) => {", moduleScript.indexOf("async function loadData")),
);
const deferred = [];
const events = [];
const sources = new Map([["climate", {setData: () => events.push("source-updated")}]]);
const layers = new Map([["border", {}], ["label", {}]]);
let activeScale = {stops: [[0, "#000000"], [12, "#ffffff"]]};
const redrawSource = moduleScript.slice(moduleScript.indexOf("function clearNoaaRaster"), moduleScript.indexOf("function formatScaleValue"));
const makeRasterFunctions = new Function("useInterpolatedNoaa", "createInterpolatedRaster", "getScale",
    `${redrawSource.replace("scale: activeScale", "scale: getScale()")}; return {clearNoaaRaster, redrawNoaaRaster};`);
const {clearNoaaRaster, redrawNoaaRaster} = makeRasterFunctions(true, ({scale}) => {
    events.push("raster-created");
    return {canvas: {scale}, coordinates: [[-1, 1], [1, 1], [1, -1], [-1, -1]]};
}, () => activeScale);
const fakeSelection = {
    beginLoading: () => events.push("loading"),
    acceptData: () => events.push("accepted"),
    fail: () => events.push("failed"),
};
const makeFunctions = new Function(
    "selection", "climateType", "fetch", "AbortController", "URLSearchParams", "formatStep",
    "useInterpolatedNoaa", "clearNoaaRaster", "redrawNoaaRaster",
    `${functionsSource}\nreturn {startViewportLoad, invalidateViewport};`,
);
const functions = makeFunctions(fakeSelection, "temp_mean", () => new Promise((resolve, reject) => {
    deferred.push({resolve, reject});
}), AbortController, URLSearchParams, value => String(value), true, clearNoaaRaster, redrawNoaaRaster);
const panel = {
    month: "1990-01", status: {textContent: ""}, moveTimer: undefined,
    viewportGeneration: 0, viewportDirty: false,
    overlayLayers: ["border", "label"],
    map: {
        getBounds: () => ({getSouth: () => -1, getWest: () => -1, getNorth: () => 1, getEast: () => 1}),
        getZoom: () => 3,
        getCanvas: () => ({clientWidth: 1200, clientHeight: 800}),
        getSource: id => sources.get(id),
        getLayer: id => layers.get(id),
        addSource: (id, source) => { assert.equal(sources.has(id), false); sources.set(id, source); events.push("source-added"); },
        removeSource: id => { sources.delete(id); events.push("source-removed"); },
        addLayer: layer => { layers.set(layer.id, layer); events.push("layer-added"); },
        removeLayer: id => { layers.delete(id); events.push("layer-removed"); },
        moveLayer: id => events.push(`above:${id}`),
    },
};
const flushAsync = async () => {
    for (let index = 0; index < 6; index += 1) await Promise.resolve();
};

functions.startViewportLoad(panel);
assert.equal(deferred.length, 1);
functions.invalidateViewport(panel);
assert.equal(events.filter(event => event === "loading").length, 2,
    "selection becomes loading synchronously on invalidation, before the delayed reload");
deferred[0].resolve({ok: true, json: async () => ({
    features: [], metadata: {provider: "test", tiles: 0, rows: 0, columns: 0,
        latitude_step: 1, longitude_step: 1, direct: 0, reused_nearby: 0, missing: 0},
})});
await flushAsync();
assert.equal(events.includes("accepted"), false, "an obsolete success cannot update selection data");

functions.startViewportLoad(panel);
assert.equal(deferred.length, 2);
functions.invalidateViewport(panel);
deferred[1].reject(new Error("stale fake failure"));
await flushAsync();
assert.equal(events.includes("failed"), false, "an obsolete failure cannot replace loading state");

const payload = {features: [], interpolation: {latitudes: [0, 2], longitudes: [0, 4], values: [[0, 4], [8, 12]]},
    metadata: {provider: "noaa_core"}};
functions.startViewportLoad(panel);
deferred[2].resolve({ok: true, json: async () => payload});
await flushAsync();
assert.equal(events.filter(event => event === "accepted").length, 1);
assert.equal(panel.interpolation, payload.interpolation);
assert.match(panel.status.textContent, /Smooth display — interpolated estimate.*2° × 4° source spacing/);
const firstSource = sources.get("climate-raster");
assert.equal(firstSource.animate, false);
assert.equal(firstSource.type, "canvas");
assert.equal(layers.get("climate-raster").paint["raster-opacity"], 1);
assert.deepEqual(events.slice(-3), ["layer-added", "above:border", "above:label"]);
activeScale = {stops: [[0, "#ff0000"], [12, "#0000ff"]]};
redrawNoaaRaster(panel);
assert.notEqual(sources.get("climate-raster"), firstSource, "static canvas source is freshly recreated");
assert.equal(sources.get("climate-raster").canvas.scale, activeScale);
assert.equal(deferred.length, 3, "manual scale redraw never fetches");
const scaleFunction = moduleScript.slice(moduleScript.indexOf("function setActiveScale"), moduleScript.indexOf("Object.values(SCALE_PRESETS"));
assert.match(scaleFunction, /redrawNoaaRaster\(panel\)/);
assert.doesNotMatch(scaleFunction, /fetch\(|loadData\(|startViewportLoad\(/);
functions.invalidateViewport(panel);
assert.equal(sources.has("climate-raster"), false);
assert.equal(panel.interpolation, null);
assert.equal(panel.rasterBounds, null);
functions.startViewportLoad(panel);
deferred[3].reject(new Error("current fake failure"));
await flushAsync();
assert.equal(events.filter(event => event === "failed").length, 1);
assert.equal(sources.has("climate-raster"), false);
functions.startViewportLoad(panel);
deferred[4].resolve({ok: true, json: async () => ({...payload, interpolation: {...payload.interpolation, values: [[null, null], [null, null]]}})});
await flushAsync();
assert.equal(sources.has("climate-raster"), false);
assert.equal(panel.interpolation, null);
assert.match(panel.status.textContent, /No saved source nodes/);
assert.match(moduleScript, /"fill-opacity": useInterpolatedNoaa \? 0 : \[\s*"case",/);
assert.match(moduleScript, /setPaintProperty\(layer\.id, "fill-color", "#e8e8e8"\)/);
assert.match(moduleScript, /setPaintProperty\(layer\.id, "fill-opacity", 1\)/);

console.log("Map template wiring preserves debounced loading, stale guards, cleanup, and fixed scale.");
