import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const template = await readFile(new URL("../templates/maps.html", import.meta.url), "utf8");
const moduleScript = template.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(moduleScript, "map page has its module script");

assert.match(template, /\/static\/map_selection\.js/);
assert.match(moduleScript, /const selection = createMapSelection\(\{panels, Popup, document, unit: activeScale\.unit\}\)/);
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
const fakeSelection = {
    beginLoading: () => events.push("loading"),
    acceptData: () => events.push("accepted"),
    fail: () => events.push("failed"),
};
const makeFunctions = new Function(
    "selection", "climateType", "fetch", "AbortController", "URLSearchParams", "formatStep",
    `${functionsSource}\nreturn {startViewportLoad, invalidateViewport};`,
);
const functions = makeFunctions(fakeSelection, "temp_mean", () => new Promise((resolve, reject) => {
    deferred.push({resolve, reject});
}), AbortController, URLSearchParams, value => String(value));
const panel = {
    month: "1990-01", status: {textContent: ""}, moveTimer: undefined,
    viewportGeneration: 0, viewportDirty: false,
    map: {
        getBounds: () => ({getSouth: () => -1, getWest: () => -1, getNorth: () => 1, getEast: () => 1}),
        getZoom: () => 3,
        getSource: () => ({setData: () => events.push("source-updated")}),
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

console.log("Map template wiring preserves debounced loading, stale guards, cleanup, and fixed scale.");
