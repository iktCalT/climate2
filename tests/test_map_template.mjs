import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {test} from "node:test";

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
    styleReady: true,
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

const scaleSource = await readFile(new URL("../static/map_scales.js", import.meta.url), "utf8");
const {presetScale, createCustomScale, customScaleFromScale, colorExpression} = await import(
    `data:text/javascript;base64,${Buffer.from(scaleSource).toString("base64")}`);
const scaleFunctions = moduleScript.slice(moduleScript.indexOf("function clearNoaaRaster"),
    moduleScript.indexOf("Object.values(SCALE_PRESETS"));
const lifecycleSource = moduleScript.slice(moduleScript.indexOf("panels.forEach((panel) => {", moduleScript.indexOf("function invalidateViewport")));

for (const useInterpolatedNoaa of [true, false]) test(`${useInterpolatedNoaa ? "NOAA" : "CMIP6"} actual scale handler synchronizes initialized panels while sources load`, () => {
    function element() {
        return {style: {}, children: [], textContent: "", append(...children) {this.children.push(...children);},
            replaceChildren(...children) {this.children = children;}};
    }
    function makePanel(styleReady, withData = true) {
        const sources = new Map();
        const layers = new Map(styleReady ? [["climate-cells", {paint: {}}]] : []);
        const handlers = {};
        const mutations = [];
        return {styleReady, interpolation: withData ? payload.interpolation : null,
            rasterBounds: withData ? {west: 0, east: 4, south: 0, north: 2} : null,
            overlayLayers: [], viewportGeneration: 0, sources, layers, handlers, mutations,
            map: {
                on: (event, callback) => {handlers[event] = callback;},
                isStyleLoaded: () => false,
                isStyleLoadedCalls: 0,
                getLayer: id => layers.get(id), getSource: id => sources.get(id),
                getCanvas: () => ({clientWidth: 500, clientHeight: 300}),
                addSource: (id, source) => {sources.set(id, source); mutations.push("addSource");},
                removeSource: id => {sources.delete(id); mutations.push("removeSource");},
                addLayer: layer => {layers.set(layer.id, layer); mutations.push("addLayer");},
                removeLayer: id => {layers.delete(id); mutations.push("removeLayer");},
                moveLayer: () => mutations.push("moveLayer"),
                setPaintProperty: (id, key, value) => {layers.get(id).paint[key] = value; mutations.push("paint");},
                setProjection: () => {}, getStyle: () => ({layers: []}), addControl: () => {},
            }};
    }
    const ready = makePanel(true);
    const preload = makePanel(false);
    const removed = makePanel(true);
    const cleared = makePanel(true, false);
    const panels = [ready, preload, removed, cleared];
    let fullLoadedChecks = 0;
    for (const panel of panels) panel.map.isStyleLoaded = () => {fullLoadedChecks += 1; return false;};
    const ui = Object.fromEntries(["presetPicker", "customFields", "minimumInput", "maximumInput", "lowColorInput",
        "middleColorInput", "highColorInput", "scaleError", "scaleSummary", "scaleLegend"].map(key => [key, element()]));
    const saved = [];
    const firstRenders = [];
    let requests = 0;
    let aborted = 0;
    removed.requestController = {abort: () => {aborted += 1;}};
    const build = new Function("env", `
        const {panels, useInterpolatedNoaa, document, family, customScaleFromScale, colorExpression,
            saveScale, createInterpolatedRaster, NavigationControl, FullscreenControl, selection,
            startViewportLoad, invalidateViewport, syncViewports, fetch,
            presetPicker, customFields, minimumInput, maximumInput, lowColorInput, middleColorInput,
            highColorInput, scaleError, scaleSummary, scaleLegend} = env;
        let activeScale = env.initialScale;
        ${scaleFunctions}
        ${lifecycleSource}
        return {setActiveScale, redrawNoaaRaster, clearNoaaRaster, currentScale: () => activeScale};`);
    const harness = build({...ui, panels, useInterpolatedNoaa, family: "temperature", document: {createElement: element},
        initialScale: presetScale("temperature"), customScaleFromScale, colorExpression,
        saveScale: (family, scale) => saved.push({family, scale}),
        createInterpolatedRaster: ({scale}) => ({canvas: {scale}, coordinates: []}),
        NavigationControl: class {}, FullscreenControl: class {},
        selection: {removePanel: panel => {assert.equal(panel, removed);}, select: () => {}},
        startViewportLoad: panel => firstRenders.push(panel.layers.get("climate-cells").paint["fill-color"]),
        invalidateViewport: () => {}, syncViewports: () => {}, fetch: () => {requests += 1; throw new Error("unexpected fetch");},
    });
    removed.handlers.remove();
    assert.equal(removed.styleReady, false);
    assert.equal(removed.interpolation, null);
    assert.equal(removed.rasterBounds, null);
    assert.equal(aborted, 1);
    const choices = [presetScale("temperature", "detail_cold"),
        createCustomScale("temperature", {min: -5, max: 15, lowColor: "#000000", midColor: "#ffffff", highColor: "#ff0000"}),
        presetScale("temperature", "detail_warm"),
        createCustomScale("temperature", {min: 5, max: 25, lowColor: "#0000ff", midColor: "#00ff00", highColor: "#ffff00"})];
    for (const scale of choices) {
        harness.setActiveScale(scale);
        assert.equal(harness.currentScale(), scale);
        assert.equal(saved.at(-1).scale, scale);
        assert.equal(ui.presetPicker.value, scale.id);
        assert.equal(ui.customFields.hidden, scale.id !== "custom");
        assert.match(ui.scaleSummary.textContent, new RegExp(`${scale.min} to ${scale.max}`));
        assert.deepEqual(ui.scaleLegend.children.map(stop => stop.children[0].style.backgroundColor), scale.stops.map(stop => stop[1]));
        assert.deepEqual(ui.scaleLegend.children.map(stop => stop.children[1].textContent), scale.stops.map(([value]) => `${value} °C`));
        if (useInterpolatedNoaa) {
            assert.equal(ready.sources.get("climate-raster").canvas.scale, scale);
            assert.equal(cleared.sources.has("climate-raster"), false, "cleared viewport cannot resurrect data");
        } else {
            assert.deepEqual(ready.layers.get("climate-cells").paint["fill-color"], colorExpression(scale));
        }
        assert.equal(preload.mutations.length, 0, "uninitialized map remains untouched");
        assert.equal(removed.mutations.length, 0, "removed map remains untouched");
    }
    assert.equal(fullLoadedChecks, 0, "source loading never gates scale mutations");
    assert.equal(requests, 0);
    assert.equal(saved.length, choices.length);
    assert.equal(ui.minimumInput.value, choices.at(-1).min);
    assert.equal(ui.maximumInput.value, choices.at(-1).max);
    preload.handlers.load();
    assert.equal(preload.styleReady, true);
    assert.deepEqual(firstRenders, [colorExpression(choices.at(-1))], "initial load uses latest pre-load choice");
    harness.redrawNoaaRaster(preload);
    if (useInterpolatedNoaa) assert.equal(preload.sources.get("climate-raster").canvas.scale, choices.at(-1));
    assert.equal(removed.mutations.length, 0);
    assert.equal(cleared.interpolation, null);
});

console.log("Map template wiring preserves debounced loading, stale guards, cleanup, and fixed scale.");
