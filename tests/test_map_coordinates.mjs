import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {test} from "node:test";

const template = await readFile(new URL("../templates/maps.html", import.meta.url), "utf8");
const moduleScript = template.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(moduleScript, "open Maps page has its module script");

function extract(start, end) {
    const first = moduleScript.indexOf(start);
    const last = moduleScript.indexOf(end, first);
    assert.notEqual(first, -1, `template contains ${start}`);
    assert.notEqual(last, -1, `template contains ${end}`);
    return moduleScript.slice(first, last);
}

const readinessSource = extract("function livePanels()", "coordinateForm.addEventListener(\"submit\"");
const submitBinding = extract("coordinateForm.addEventListener(\"submit\"", "clearCoordinateButton.addEventListener(\"click\"");
const clearBinding = extract("clearCoordinateButton.addEventListener(\"click\"", "function clearNoaaRaster");
const syncSource = extract("function syncViewports(", "async function loadData(");
const panelBindings = moduleScript.slice(moduleScript.indexOf("panels.forEach((panel) => {\n                panel.retryButton.addEventListener"));

function makeHarness(count, {sameCenter = false} = {}) {
    const selectionCalls = [];
    let fetches = 0;
    const panels = [];
    const mapMutations = [];
    const elements = {
        coordinateForm: {listeners: {}, addEventListener(name, callback) {this.listeners[name] = callback;}},
        latitudeInput: {value: ""}, longitudeInput: {value: ""},
        showCoordinateButton: {disabled: true}, clearCoordinateButton: {listeners: {}, addEventListener(name, callback) {this.listeners[name] = callback;}},
        coordinateStatus: {textContent: "Waiting for all map panels to initialize…"},
    };
    for (let index = 0; index < count; index += 1) {
        const handlers = {};
        const startView = {lng: -98.5, lat: 39.5, zoom: 3.25, bearing: 12, pitch: 18};
        let center = {lng: sameCenter && index === 0 ? -20.25 : startView.lng,
            lat: sameCenter && index === 0 ? 34.5 : startView.lat};
        const map = {
            on(name, callback) {handlers[name] = callback;},
            getCenter() {return {...center};},
            getZoom() {return startView.zoom;}, getBearing() {return startView.bearing;}, getPitch() {return startView.pitch;},
            jumpTo(view) {
                const previous = center;
                mapMutations.push({index, view: structuredClone(view)});
                center = Array.isArray(view.center)
                    ? {lng: view.center[0], lat: view.center[1]}
                    : {lng: view.center.lng, lat: view.center.lat};
                startView.zoom = view.zoom; startView.bearing = view.bearing; startView.pitch = view.pitch;
                if (handlers.move && (previous.lng !== center.lng || previous.lat !== center.lat)) handlers.move();
            },
            getStyle() {return {layers: []};}, setProjection() {}, setPaintProperty() {}, addControl() {},
            addSource() {}, addLayer() {}, getLayer() {return undefined;}, getSource() {return undefined;},
        };
        const panel = {month: `200${index}-01`, map, handlers, styleReady: false, removed: false,
            status: {textContent: ""}, retryButton: {hidden: true, disabled: true, addEventListener(_name, callback) {this.click = callback;}},
            overlayLayers: [], moveTimer: undefined, requestController: undefined, viewportGeneration: 0,
            interpolation: null, rasterBounds: null};
        panels.push(panel);
        panel.initialView = {...startView};
    }

    let retryCallback;
    const syncHarness = new Function("panels", `let synchronizingViewports = false; ${syncSource}; return syncViewports;`)(panels);
    // Keep the exact page function as the sole readiness implementation and expose its state transitions.
    const makeBindings = new Function(
        "panels", "selection", "syncViewports", "coordinateForm", "latitudeInput",
        "longitudeInput", "showCoordinateButton", "clearCoordinateButton", "coordinateStatus",
        `let coordinateReadiness; ${readinessSource}\n${submitBinding}\n${clearBinding}\nreturn {updateCoordinateReadiness};`,
    );
    const readiness = makeBindings(panels, {
        select: point => selectionCalls.push({type: "select", point}),
        clear: () => selectionCalls.push({type: "clear"}),
        removePanel: panel => selectionCalls.push({type: "remove", panel}),
        beginLoading: () => {}, fail: () => {},
    }, syncHarness,
    elements.coordinateForm, elements.latitudeInput, elements.longitudeInput, elements.showCoordinateButton,
    elements.clearCoordinateButton, elements.coordinateStatus);

    // Capture the template's actual ready/removal lifecycle callbacks and per-panel UI bindings.
    const lifecycleEnv = {
        panels,
        updateCoordinateReadiness: readiness.updateCoordinateReadiness,
        selection: {
            select: point => selectionCalls.push({type: "select", point}),
            clear: () => selectionCalls.push({type: "clear"}),
            removePanel: panel => selectionCalls.push({type: "remove", panel}),
            beginLoading: () => {}, fail: () => {},
        },
        retrySavedData: panel => {retryCallback = panel;}, resetRetry: () => {}, startViewportLoad: () => {fetches += 1;},
        invalidateViewport: () => {}, syncViewports: syncHarness, clearTimeout: () => {},
        useInterpolatedNoaa: false, activeScale: {}, colorExpression: () => [],
        NavigationControl: class {}, FullscreenControl: class {},
    };
    new Function("panels", "selection", "retrySavedData", "resetRetry", "startViewportLoad", "invalidateViewport",
        "syncViewports", "clearTimeout", "useInterpolatedNoaa", "activeScale", "colorExpression", "NavigationControl",
        "FullscreenControl", "updateCoordinateReadiness", `${panelBindings};`)(...[
        lifecycleEnv.panels, lifecycleEnv.selection, lifecycleEnv.retrySavedData, lifecycleEnv.resetRetry,
        lifecycleEnv.startViewportLoad, lifecycleEnv.invalidateViewport, lifecycleEnv.syncViewports,
        lifecycleEnv.clearTimeout, lifecycleEnv.useInterpolatedNoaa, lifecycleEnv.activeScale,
        lifecycleEnv.colorExpression, lifecycleEnv.NavigationControl, lifecycleEnv.FullscreenControl,
        lifecycleEnv.updateCoordinateReadiness,
    ]);

    return {
        ...elements, panels, selectionCalls, mapMutations, get fetches() {return fetches;},
        prevented: 0,
        fireSubmit() {elements.coordinateForm.listeners.submit({preventDefault: () => {this.prevented += 1;}});},
        fireClear() {elements.clearCoordinateButton.listeners.click();},
        fireLoad(panel) {panel.handlers.load();}, fireRemove(panel) {panel.handlers.remove();},
    };
}

test("coordinate submit rejects blank, nonfinite, and out-of-range inputs without map or selection changes", () => {
    const harness = makeHarness(1);
    harness.fireLoad(harness.panels[0]);
    const invalid = [
        ["", "12"], ["12", "  "], ["NaN", "1"], ["1", "Infinity"],
        ["-85.0001", "0"], ["85.0001", "0"], ["0", "-180.0001"], ["0", "180.0001"],
    ];
    for (const [latitude, longitude] of invalid) {
        harness.latitudeInput.value = latitude;
        harness.longitudeInput.value = longitude;
        harness.fireSubmit();
        assert.match(harness.coordinateStatus.textContent, /Enter a latitude/);
        assert.equal(harness.latitudeInput.value, latitude, "invalid latitude text is retained");
        assert.equal(harness.longitudeInput.value, longitude, "invalid longitude text is retained");
        assert.equal(harness.mapMutations.length, 0);
        assert.equal(harness.selectionCalls.length, 0);
    }
});

test("inclusive decimal endpoints submit; valid submissions preserve view and synchronize one/four panels", () => {
    for (const count of [1, 4]) {
        const harness = makeHarness(count, {sameCenter: true});
        for (const panel of harness.panels) harness.fireLoad(panel);
        assert.equal(harness.showCoordinateButton.disabled, false);
        assert.equal(harness.coordinateStatus.textContent, "Enter coordinates to show a location on the maps.");
        harness.latitudeInput.value = "-85";
        harness.longitudeInput.value = "180";
        harness.fireSubmit();
        assert.equal(harness.prevented, 1, "native form navigation is prevented");
        assert.equal(harness.selectionCalls.filter(call => call.type === "select").length, 1);
        assert.deepEqual(harness.selectionCalls.find(call => call.type === "select").point, {lng: 180, lat: -85});
        assert.equal(harness.mapMutations.length, count, "every live panel receives the same requested center");
        assert.ok(harness.mapMutations.every(({view}) => {
            const center = Array.isArray(view.center) ? {lng: view.center[0], lat: view.center[1]} : view.center;
            return center.lng === 180 && center.lat === -85;
        }));
        for (const panel of harness.panels) {
            assert.deepEqual([panel.map.getZoom(), panel.map.getBearing(), panel.map.getPitch()],
                [panel.initialView.zoom, panel.initialView.bearing, panel.initialView.pitch]);
        }
        assert.match(harness.coordinateStatus.textContent, /Showing -85° latitude, 180° longitude/);

        harness.latitudeInput.value = "12.375";
        harness.longitudeInput.value = "-45.625";
        harness.fireSubmit();
        assert.ok(harness.panels.every(panel => panel.map.getCenter().lng === -45.625 && panel.map.getCenter().lat === 12.375));
        assert.ok(harness.mapMutations.every(({view}) => view.zoom !== undefined && view.bearing !== undefined && view.pitch !== undefined));
    }
});

test("submitting the source panel's existing center still synchronizes comparison peers", () => {
    const harness = makeHarness(4, {sameCenter: true});
    for (const panel of harness.panels) harness.fireLoad(panel);
    harness.latitudeInput.value = "34.5";
    harness.longitudeInput.value = "-20.25";
    harness.fireSubmit();
    assert.equal(harness.mapMutations.filter(({index}) => index === 0).length, 1,
        "source panel receives the explicit center submission");
    assert.equal(harness.mapMutations.length, 4,
        "the already-centered path explicitly synchronizes all three peers");
    assert.ok(harness.panels.every(panel => panel.map.getCenter().lng === -20.25 && panel.map.getCenter().lat === 34.5));
});

test("readiness gates submission, rechecks stale readiness, and removal excludes dead panels", () => {
    const harness = makeHarness(4);
    harness.latitudeInput.value = "25.5";
    harness.longitudeInput.value = "-70.25";
    harness.fireLoad(harness.panels[0]);
    harness.fireLoad(harness.panels[1]);
    assert.equal(harness.showCoordinateButton.disabled, true);
    assert.match(harness.coordinateStatus.textContent, /Waiting for all map panels/);
    harness.fireSubmit();
    assert.match(harness.coordinateStatus.textContent, /still initializing/);
    assert.equal(harness.mapMutations.length, 0);
    assert.equal(harness.selectionCalls.length, 0);
    harness.fireLoad(harness.panels[2]);
    harness.fireLoad(harness.panels[3]);
    assert.equal(harness.showCoordinateButton.disabled, false, "all-ready transition enables submission");

    harness.panels[2].styleReady = false;
    harness.fireRemove(harness.panels[3]);
    assert.equal(harness.showCoordinateButton.disabled, true, "removing a panel updates readiness");
    assert.match(harness.coordinateStatus.textContent, /Waiting for all map panels/);
    harness.fireSubmit();
    assert.match(harness.coordinateStatus.textContent, /still initializing/);
    assert.equal(harness.showCoordinateButton.disabled, true, "submit rechecks live panel readiness");
    assert.equal(harness.mapMutations.length, 0);

    harness.panels[2].styleReady = true;
    harness.fireSubmit();
    assert.ok(harness.mapMutations.length > 0);
    assert.ok(harness.mapMutations.every(({index}) => index !== 3), "removed map receives no movement");
    for (const panel of harness.panels.slice(0, 3)) harness.fireRemove(panel);
    assert.equal(harness.showCoordinateButton.disabled, true, "removing every panel keeps submit disabled");
    const mutationCount = harness.mapMutations.length;
    harness.fireSubmit();
    assert.equal(harness.mapMutations.length, mutationCount, "all-removed maps receive no operations");
});

test("clear closes readouts only, without pan, request, or scale changes", () => {
    const harness = makeHarness(2);
    for (const panel of harness.panels) harness.fireLoad(panel);
    harness.fireClear();
    assert.deepEqual(harness.selectionCalls.map(call => call.type), ["clear"]);
    assert.equal(harness.mapMutations.length, 0);
    assert.equal(harness.fetches, 2, "only initialization loads occurred; clear adds no fetch");
    assert.equal(harness.coordinateStatus.textContent, "Location readouts cleared.");
});
