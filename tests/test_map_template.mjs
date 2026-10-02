import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {test} from "node:test";

const template = await readFile(new URL("../templates/maps.html", import.meta.url), "utf8");
const moduleScript = template.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(moduleScript, "map page has its module script");

assert.match(template, /\/static\/map_selection\.js/);
assert.match(template, /<button id="map-retry-\{\{ loop\.index0 \}\}"[\s\S]*?type="button"[\s\S]*?aria-label="Retry saved data for \{\{ panel_month \}\}"[\s\S]*?aria-describedby="map-status-\{\{ loop\.index0 \}\}" hidden>Retry saved data<\/button>/,
    "each month has a native, initially hidden retry button associated with its status");
assert.match(moduleScript, /const selection = createMapSelection\(\{\s*panels, Popup, document, unit: activeScale\.unit,\s*sample: useInterpolatedNoaa \? sampleGrid : undefined,/);
assert.match(moduleScript, /panel\.map\.on\("click", event => \{\s*if \(!communityPins\.handleMapClick\(event\)\) selection\.select\(event\.lngLat\);\s*\}\)/);
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
    moduleScript.indexOf("function resetRetry"),
    moduleScript.indexOf("panels.forEach((panel) => {", moduleScript.indexOf("async function loadData")),
);
const deferred = [];
const events = [];
let canceledTimer;
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
    "selection", "climateType", "fetch", "AbortController", "URLSearchParams", "formatStep", "clearTimeout",
    "useInterpolatedNoaa", "clearNoaaRaster", "redrawNoaaRaster",
    `${functionsSource}\nreturn {startViewportLoad, invalidateViewport, retrySavedData, loadData};`,
);
const functions = makeFunctions(fakeSelection, "temp_mean", () => new Promise((resolve, reject) => {
    deferred.push({resolve, reject});
}), AbortController, URLSearchParams, value => String(value), timer => {canceledTimer = timer; timers?.delete(timer);},
true, clearNoaaRaster, redrawNoaaRaster);
const panel = {
    month: "1990-01", status: {textContent: ""}, retryButton: {hidden: true, disabled: true}, moveTimer: undefined,
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
assert.equal(panel.requestController.signal.aborted, true);
assert.equal(panel.retryButton.hidden, true);
assert.equal(panel.retryButton.disabled, true);
assert.equal(events.filter(event => event === "loading").length, 2,
    "selection becomes loading synchronously on invalidation, before the delayed reload");
deferred[0].resolve({ok: true, json: async () => ({
    features: [], metadata: {provider: "test", tiles: 0, rows: 0, columns: 0,
        latitude_step: 1, longitude_step: 1, direct: 0, reused_nearby: 0, missing: 0},
})});
await flushAsync();
assert.equal(events.includes("accepted"), false, "an obsolete success cannot update selection data");
assert.match(panel.status.textContent, /Loading viewport data/,
    "a response resolving after abort cannot alter the current status");
assert.equal(panel.retryButton.hidden, true, "an aborted request cannot reveal retry");
assert.equal(panel.retryButton.disabled, true);

functions.startViewportLoad(panel);
assert.equal(deferred.length, 2);
functions.invalidateViewport(panel);
assert.equal(panel.requestController.signal.aborted, true);
deferred[1].reject(new DOMException("request canceled", "AbortError"));
await flushAsync();
assert.equal(events.includes("failed"), false, "an obsolete failure cannot replace loading state");
assert.match(panel.status.textContent, /Loading viewport data/,
    "an AbortError after invalidation leaves the current status alone");
assert.equal(panel.retryButton.hidden, true, "an AbortError does not offer retry");
assert.equal(panel.retryButton.disabled, true);

const payload = {features: [], interpolation: {latitudes: [0, 2], longitudes: [0, 4], values: [[0, 4], [8, 12]]},
    metadata: {provider: "noaa_core"}};
functions.startViewportLoad(panel);
deferred[2].resolve({ok: true, json: async () => payload});
await flushAsync();
assert.equal(events.filter(event => event === "accepted").length, 1);
assert.equal(panel.interpolation, payload.interpolation);
assert.match(panel.status.textContent, /Smooth display — interpolated estimate.*Saved sampling grid: 2° latitude × 4° longitude/);
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

// Exercise the actual extracted load/retry functions with a one-panel failure → retry → success flow.
panel.map.getBounds = () => ({getSouth: () => -1, getWest: () => -1, getNorth: () => 1, getEast: () => 1});
functions.startViewportLoad(panel);
deferred[5].reject(new Error("temporary outage"));
await flushAsync();
assert.equal(panel.retryButton.hidden, false, "current request failures reveal the retry control");
assert.equal(panel.retryButton.disabled, false);
assert.match(panel.status.textContent, /Map data unavailable: temporary outage/);
const originalMonth = panel.month;
const originalBounds = panel.map.getBounds();
const otherPanel = {month: "1991-02", removed: false, styleReady: true,
    retryButton: {hidden: false, disabled: false, addEventListener(_event, callback) {this.click = callback;}},
    viewportGeneration: 8};
let clickRetry;
panel.retryButton.addEventListener = (_name, callback) => { clickRetry = callback; };
const actualClickBinding = moduleScript.slice(moduleScript.indexOf("panel.retryButton.addEventListener"),
    moduleScript.indexOf('panel.map.on("load"', moduleScript.indexOf("panel.retryButton.addEventListener")));
new Function("panels", "retrySavedData", `panels.forEach((panel) => { ${actualClickBinding} });`)(
    [panel, otherPanel], functions.retrySavedData);
assert.equal(typeof clickRetry, "function", "the template's actual native click listener is installed");
assert.equal(typeof otherPanel.retryButton.click, "function", "the other real panel has its own bound retry listener");
const timers = new Map();
let nextTimer = 122;
const moveendBinding = moduleScript.slice(moduleScript.indexOf('panel.map.on("moveend"'),
    moduleScript.indexOf('panel.map.on("remove"'));
panel.map.on = (event, callback) => {panel.map.moveend = event === "moveend" ? callback : panel.map.moveend;};
new Function("panel", "setTimeout", "clearTimeout", "startViewportLoad", moveendBinding)(
    panel,
    callback => {nextTimer += 1; timers.set(nextTimer, callback); return nextTimer;},
    timer => timers.delete(timer), functions.startViewportLoad,
);
panel.map.moveend();
assert.equal(timers.size, 1, "moveend schedules one debounced request");
panel.moveTimer = [...timers.keys()][0];
clickRetry();
assert.equal(canceledTimer, 123, "manual retry cancels a pending movement debounce");
assert.equal(panel.moveTimer, undefined);
assert.equal(timers.size, 0, "the pending movement callback is removed when retry starts");
assert.equal(panel.retryButton.disabled, true, "retry disables rapid repeated clicks");
assert.equal(deferred.length, 7);
clickRetry();
assert.equal(deferred.length, 7, "a second click while retrying does not issue another request");
assert.equal(panel.month, originalMonth);
assert.deepEqual([panel.map.getBounds().getSouth(), panel.map.getBounds().getWest(),
    panel.map.getBounds().getNorth(), panel.map.getBounds().getEast()],
    [originalBounds.getSouth(), originalBounds.getWest(), originalBounds.getNorth(), originalBounds.getEast()]);
deferred[6].resolve({ok: true, json: async () => payload});
await flushAsync();
assert.equal(panel.retryButton.hidden, true, "success hides the retry control");
assert.equal(panel.retryButton.disabled, true);
assert.equal(events.filter(event => event === "accepted").length, 3);

functions.startViewportLoad(panel);
deferred[7].reject(new Error("still offline"));
await flushAsync();
assert.equal(panel.retryButton.hidden, false, "a later failure makes retry available again");
assert.equal(panel.retryButton.disabled, false);

// Empty coverage is a successful response and invalid bounds return before fetch; neither offers retry.
functions.retrySavedData(panel);
deferred[8].resolve({ok: true, json: async () => ({features: [], metadata: {provider: "test", tiles: 0,
    rows: 0, columns: 0, latitude_step: 1, longitude_step: 1, direct: 0, reused_nearby: 0, missing: 0}})});
await flushAsync();
assert.equal(panel.retryButton.hidden, true, "valid empty coverage does not offer retry");
panel.map.getBounds = () => ({getSouth: () => 89, getWest: () => -1, getNorth: () => 90, getEast: () => 1});
functions.startViewportLoad(panel);
assert.equal(deferred.length, 9, "invalid bounds do not issue a request");
assert.equal(panel.retryButton.hidden, true, "invalid bounds do not offer retry");
assert.match(panel.status.textContent, /Move the map back/);
assert.deepEqual({month: otherPanel.month, hidden: otherPanel.retryButton.hidden,
    disabled: otherPanel.retryButton.disabled, generation: otherPanel.viewportGeneration},
    {month: "1991-02", hidden: false, disabled: false, generation: 8},
    "retry leaves every other comparison panel untouched");
panel.map.getBounds = () => ({getSouth: () => -1, getWest: () => -1, getNorth: () => 1, getEast: () => 1});
functions.startViewportLoad(panel);
const obsoleteController = panel.requestController;
functions.startViewportLoad(panel);
const currentController = panel.requestController;
deferred[9].reject(new Error("obsolete failure"));
await flushAsync();
assert.equal(panel.requestController, currentController, "an obsolete finally block cannot clear the active request");
assert.match(panel.status.textContent, /Loading viewport data/,
    "an obsolete failure cannot replace the current loading state");
deferred[10].resolve({ok: true, json: async () => payload});
await flushAsync();
assert.equal(panel.requestController, undefined);
assert.notEqual(obsoleteController, currentController);
for (const unavailable of [
    {removed: true, styleReady: false, retryButton: {hidden: false, disabled: false}},
    {removed: false, styleReady: false, retryButton: {hidden: false, disabled: false}},
]) {
    const generation = unavailable.viewportGeneration;
    functions.retrySavedData(unavailable);
    functions.startViewportLoad(unavailable);
    assert.equal(unavailable.viewportGeneration, generation, "removed or uninitialized panels refuse retry/load");
}
assert.match(moduleScript, /"fill-opacity": useInterpolatedNoaa \? 0 : \[\s*"case",/);
assert.match(moduleScript, /setPaintProperty\(layer\.id, "fill-color", "#e8e8e8"\)/);
assert.match(moduleScript, /setPaintProperty\(layer\.id, "fill-opacity", 1\)/);

const scaleSource = await readFile(new URL("../static/map_scales.js", import.meta.url), "utf8");
const {presetScale, createCustomScale, customScaleFromScale, colorExpression} = await import(
    `data:text/javascript;base64,${Buffer.from(scaleSource).toString("base64")}`);
    const scaleFunctions = moduleScript.slice(moduleScript.indexOf("function clearNoaaRaster"),
    moduleScript.indexOf("Object.values(SCALE_PRESETS"));
const lifecycleSource = moduleScript.slice(moduleScript.indexOf("panels.forEach((panel) => {", moduleScript.indexOf("function invalidateViewport")));
const resetRetrySource = moduleScript.slice(moduleScript.indexOf("function resetRetry"), moduleScript.indexOf("function syncViewports"));
const readinessSource = moduleScript.slice(moduleScript.indexOf("function livePanels()"), moduleScript.indexOf("coordinateForm.addEventListener(\"submit\""));

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
        return {styleReady, retryButton: {hidden: true, disabled: true,
                addEventListener: (event, callback) => {handlers[`retry-${event}`] = callback;}},
            interpolation: withData ? payload.interpolation : null,
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
    const showCoordinateButton = {disabled: true};
    const coordinateStatus = {textContent: "Waiting for all map panels to initialize…"};
    const saved = [];
    const firstRenders = [];
    let requests = 0;
    let aborted = 0;
    removed.requestController = {abort: () => {aborted += 1;}};
    const build = new Function("env", `
        const {panels, useInterpolatedNoaa, document, family, customScaleFromScale, colorExpression,
            saveScale, createInterpolatedRaster, NavigationControl, FullscreenControl, selection,
            startViewportLoad, invalidateViewport, syncViewports, retrySavedData, fetch,
            showCoordinateButton, coordinateStatus,
            presetPicker, customFields, minimumInput, maximumInput, lowColorInput, middleColorInput,
            highColorInput, scaleError, scaleSummary, scaleLegend} = env;
        let coordinateReadiness = false;
        let activeScale = env.initialScale;
        ${scaleFunctions}
        ${resetRetrySource}
        ${readinessSource}
        ${lifecycleSource}
        return {setActiveScale, redrawNoaaRaster, clearNoaaRaster, currentScale: () => activeScale};`);
    const harness = build({...ui, panels, useInterpolatedNoaa, family: "temperature", document: {createElement: element},
        showCoordinateButton, coordinateStatus,
        initialScale: presetScale("temperature"), customScaleFromScale, colorExpression,
        saveScale: (family, scale) => saved.push({family, scale}),
        createInterpolatedRaster: ({scale}) => ({canvas: {scale}, coordinates: []}),
        NavigationControl: class {}, FullscreenControl: class {},
        selection: {removePanel: panel => {assert.equal(panel, removed);}, select: () => {}},
        startViewportLoad: panel => firstRenders.push(panel.layers.get("climate-cells").paint["fill-color"]),
        invalidateViewport: () => {}, syncViewports: () => {}, retrySavedData: () => {},
        fetch: () => {requests += 1; throw new Error("unexpected fetch");},
    });
    removed.handlers.remove();
    assert.equal(showCoordinateButton.disabled, true, "one uninitialized live panel keeps coordinate submission disabled");
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
    assert.equal(showCoordinateButton.disabled, false, "actual lifecycle binding enables submission once all live panels initialize");
    assert.equal(coordinateStatus.textContent, "Enter coordinates to show a location on the maps.");
    assert.deepEqual(firstRenders, [colorExpression(choices.at(-1))], "initial load uses latest pre-load choice");
    harness.redrawNoaaRaster(preload);
    if (useInterpolatedNoaa) assert.equal(preload.sources.get("climate-raster").canvas.scale, choices.at(-1));
    assert.equal(removed.mutations.length, 0);
    assert.equal(cleared.interpolation, null);
});

console.log("Map template wiring preserves debounced loading, stale guards, cleanup, and fixed scale.");
