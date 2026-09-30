import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const source = await readFile(new URL("../static/map_selection.js", import.meta.url), "utf8");
const {createMapSelection} = await import(
    `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);
const interpolationSource = await readFile(new URL("../static/map_interpolation.js", import.meta.url), "utf8");
const {sampleGrid} = await import(`data:text/javascript;base64,${Buffer.from(interpolationSource).toString("base64")}`);

function harness(months, unit = "°C", sample) {
    const panels = months.map(month => ({month, map: {}}));
    const popups = [];
    const document = {
        createElement(tag) {
            return {
                tag, textContent: "", children: [],
                append(child) { this.children.push(child); },
            };
        },
    };
    class Popup {
        constructor(options) { this.options = options; this.handlers = {}; this.removed = 0; popups.push(this); }
        setLngLat(value) { this.lngLat = value; return this; }
        setDOMContent(value) { this.content = value; return this; }
        addTo(map) { this.map = map; return this; }
        on(name, handler) { this.handlers[name] = handler; return this; }
        remove() { this.removed += 1; }
        close() { this.handlers.close?.(); }
        text() {
            const collect = element => [element.textContent, ...element.children.map(collect)].filter(Boolean).join("\n");
            return collect(this.content);
        }
    }
    return {panels, popups, selection: createMapSelection({panels, Popup, document, unit, sample})};
}

function feature({west, east, south, north, value, latitude, longitude, source = "direct_cache"}) {
    return {type: "Feature", geometry: {type: "Polygon", coordinates: [[
        [west, south], [east, south], [east, north], [west, north], [west, south],
    ]]}, properties: {value, latitude, longitude, source}};
}

function historyLinks(popup) {
    const collect = element => [
        ...(element.tag === "a" ? [element] : []),
        ...element.children.flatMap(collect),
    ];
    return collect(popup.content).filter(link => link.textContent === "View saved location history");
}

{
    const {panels, popups, selection} = harness(["1990-01"]);
    selection.acceptData(panels[0], {features: [feature({west: -2, east: 2, south: -2, north: 2,
        value: 0, latitude: 0.5, longitude: 0.5})]});
    selection.select({lng: 1, lat: 1});
    assert.equal(popups.length, 1);
    assert.equal(popups[0].lngLat.lng, 1);
    assert.match(popups[0].text(), /0 °C/);
    assert.match(popups[0].text(), /Grid center: 0\.5000° lat, 0\.5000° lon/);
    assert.match(popups[0].text(), /Selected: 1\.0000° lat, 1\.0000° lon/);
    assert.equal(popups[0].options.closeOnClick, false);
    assert.doesNotMatch(popups[0].text(), /Baseline|Difference from baseline/);
    assert.equal(historyLinks(popups[0]).length, 1);
    assert.equal(historyLinks(popups[0])[0].href,
        "/locations?latitude=1&longitude=1", "the URL uses the selected point, not its grid center");
    assert.match(popups[0].text(), /History uses its own sampling rule/);
}

{
    const {panels, popups, selection} = harness(["one", "two", "three", "four"]);
    selection.select({lng: -0.123456789012345, lat: 0});
    assert.equal(popups.length, 4);
    const expected = "/locations?latitude=0&longitude=-0.123456789012345";
    assert.ok(popups.every(popup => historyLinks(popup).length === 1
        && historyLinks(popup)[0].href === expected), "all panels share precise selected coordinates");
    assert.ok(popups.every((popup, index) => popup.map === panels[index].map));

    selection.select({lng: -180, lat: -90});
    assert.ok(popups.slice(-4).every(popup => historyLinks(popup)[0].href
        === "/locations?latitude=-90&longitude=-180"), "inclusive range endpoints are linkable");
    selection.select({lng: 180, lat: 90});
    assert.ok(popups.slice(-4).every(popup => historyLinks(popup)[0].href
        === "/locations?latitude=90&longitude=180"), "opposite inclusive endpoints are linkable");
}

{
    const {panels, popups, selection} = harness(["month"]);
    selection.select({lng: 0, lat: 0});
    assert.equal(historyLinks(popups.at(-1))[0].href, "/locations?latitude=0&longitude=0");
    selection.select({lng: 180.000001, lat: 0});
    assert.equal(historyLinks(popups.at(-1)).length, 0, "out-of-range coordinates have no URL");
    selection.select({lng: 0, lat: -90.000001});
    assert.equal(historyLinks(popups.at(-1)).length, 0, "out-of-range latitude has no URL");
    selection.acceptData(panels[0], {features: []});
    assert.equal(historyLinks(popups.at(-1)).length, 0);
}

{
    const {panels, popups, selection} = harness(["1990-01", "1990-02", "1990-03", "1990-04"], "mm/day");
    const cellA = feature({west: 0, east: 2, south: 0, north: 2, value: -4.1234, latitude: 1, longitude: 1});
    const cellB = feature({west: 0, east: 2, south: 0, north: 2, value: 0.2534, latitude: 1, longitude: 1,
        source: "nearby_cache"});
    panels.forEach((panel, i) => selection.acceptData(panel, {features: [i === 1 ? cellB : cellA]}));
    selection.select({lng: 0.1, lat: 0.1});
    assert.equal(popups.length, 4);
    assert.ok(popups.every(popup => popup.lngLat.lng === 0.1 && popup.lngLat.lat === 0.1));
    assert.match(popups[0].text(), /Baseline/);
    assert.match(popups[0].text(), /-4\.12 mm\/day/);
    assert.match(popups[0].text(), /Direct PostgreSQL value/);
    assert.match(popups[1].text(), /0\.25 mm\/day/);
    assert.match(popups[1].text(), /Reused nearby PostgreSQL value/);
    assert.match(popups[1].text(), /\+4\.38 mm\/day/,
        "difference uses raw inputs (-4.1234 and 0.2534) before two-place display rounding");
    assert.match(popups[2].text(), /Difference from baseline/);
    assert.match(popups[2].text(), /1990-03/);
    assert.equal(popups[4 - 1].map, panels[3].map);
}

{
    const {panels, popups, selection} = harness(["baseline", "small negative", "rounded zero", "exact zero"]);
    const values = [1, 0.995, 0.999, 1];
    panels.forEach((panel, i) => selection.acceptData(panel, {features: [feature({
        west: -1, east: 1, south: -1, north: 1, value: values[i], latitude: 0, longitude: 0,
    })]}));
    selection.select({lng: 0, lat: 0});
    assert.match(popups[1].text(), /−0\.01 °C/);
    assert.match(popups[2].text(), /0 °C/);
    assert.doesNotMatch(popups[2].text(), /−0(?:\.00)? °C/,
        "a negative raw difference that rounds to zero is displayed without negative zero");
    assert.match(popups[3].text(), /0 °C/);
    assert.doesNotMatch(popups[2].text(), /−0\.00/);
}

{
    for (const estimateIndex of [0, 1]) {
        const {panels, popups, selection} = harness(["baseline", "current"]);
        panels.forEach((panel, i) => selection.acceptData(panel, {features: [feature({
            west: -1, east: 1, south: -1, north: 1, value: i + 1, latitude: 0, longitude: 0,
            source: i === estimateIndex ? "display_estimate" : "direct_cache",
        })]}));
        selection.select({lng: 0, lat: 0});
        assert.match(popups[1].text(), /\+1 °C/);
        assert.match(popups[1].text(), /Estimate-based difference/);
    }
}

{
    const {panels, popups, selection} = harness(["baseline", "current"]);
    selection.acceptData(panels[0], {features: []});
    selection.acceptData(panels[1], {features: [feature({west: -1, east: 1, south: -1, north: 1,
        value: 2, latitude: 0, longitude: 0})]});
    selection.select({lng: 0, lat: 0});
    assert.match(popups[1].text(), /Baseline has no saved climate value/);
    assert.equal(historyLinks(popups[1]).length, 1, "missing coverage keeps the history link");
    selection.beginLoading(panels[0]);
    assert.match(popups.at(-1).text(), /Baseline is still loading/);
    assert.equal(historyLinks(popups.at(-1)).length, 1, "loading coverage keeps the history link");
    selection.fail(panels[0]);
    assert.match(popups.at(-1).text(), /Baseline map data is unavailable/);
    assert.equal(historyLinks(popups.at(-1)).length, 1, "failed coverage keeps the history link");
    selection.acceptData(panels[0], {features: [feature({west: -1, east: 1, south: -1, north: 1,
        value: Infinity, latitude: 0, longitude: 0})]});
    assert.match(popups.at(-1).text(), /Baseline has no saved climate value/);
    selection.acceptData(panels[0], {features: [feature({west: -1, east: 1, south: -1, north: 1,
        value: Number.MAX_VALUE, latitude: 0, longitude: 0})]});
    selection.acceptData(panels[1], {features: [feature({west: -1, east: 1, south: -1, north: 1,
        value: -Number.MAX_VALUE, latitude: 0, longitude: 0})]});
    assert.match(popups.at(-1).text(), /Difference unavailable because the numeric result is outside/);

    selection.acceptData(panels[0], {features: [feature({west: -1, east: 1, south: -1, north: 1,
        value: 1, latitude: 0, longitude: 0})]});
    selection.beginLoading(panels[1]);
    assert.match(popups.at(-1).text(), /This month is still loading/);
    selection.fail(panels[1]);
    assert.match(popups.at(-1).text(), /This month map data is unavailable/);
    selection.acceptData(panels[1], {features: [feature({west: -1, east: 1, south: -1, north: 1,
        value: NaN, latitude: 0, longitude: 0})]});
    assert.match(popups.at(-1).text(), /This month has no saved climate value/);
}

{
    const {panels, selection} = harness(["1990-01", "1990-02"]);
    selection.select({lng: 0, lat: 0});
    selection.removePanel(panels[1]);
    assert.doesNotThrow(() => selection.select({lng: 1, lat: 1}),
        "selecting after a panel is removed should not dereference its deleted state");
}

{
    const {panels, popups, selection} = harness(["1990-01", "1990-02"]);
    const nearbyButOutside = feature({west: 1.1, east: 1.2, south: 0, north: 0.1,
        value: 88, latitude: 0.05, longitude: 1.15});
    const containing = feature({west: -1, east: 1, south: -1, north: 1,
        value: -2, latitude: 0, longitude: 0});
    selection.acceptData(panels[0], {features: [nearbyButOutside, containing]});
    selection.acceptData(panels[1], {features: []});
    selection.select({lng: 0, lat: 0});
    assert.match(popups[0].text(), /-2 °C/);
    assert.doesNotMatch(popups[0].text(), /88 °C/);
    assert.match(popups[1].text(), /No saved climate data/);
    selection.beginLoading(panels[0]);
    assert.match(popups.findLast(popup => popup.map === panels[0].map).text(), /Loading viewport data/);
    selection.fail(panels[1]);
    assert.match(popups.findLast(popup => popup.map === panels[1].map).text(), /Map data unavailable/);
}

{
    const {panels, popups, selection} = harness(["<img onerror=alert(1)>"]);
    selection.acceptData(panels[0], {features: [feature({west: -1, east: 1, south: -1, north: 1,
        value: NaN, latitude: 0, longitude: 0})]});
    selection.select({lng: 0, lat: 0});
    assert.equal(popups[0].content.children[0].textContent, "<img onerror=alert(1)>");
    assert.match(popups[0].text(), /No saved climate data/);
    assert.ok(popups[0].content.children.every(child => !("innerHTML" in child)));
    selection.select({lng: 0.2, lat: 0.2});
    assert.ok(popups.slice(0, 1).every(popup => popup.removed === 1));
    selection.clear();
    assert.ok(popups.every(popup => popup.removed >= 1));
}

{
    const {panels, popups, selection} = harness(["1990-01", "1990-02"]);
    selection.select({lng: 4, lat: 5});
    assert.ok(popups.every(popup => /Loading viewport data/.test(popup.text())));
    assert.ok(popups.every(popup => historyLinks(popup).length === 1));
    popups[0].close();
    const afterClose = popups.length;
    selection.acceptData(panels[0], {features: []});
    assert.equal(popups.length, afterClose);
    selection.select({lng: 0, lat: 0});
    selection.removePanel(panels[1]);
    assert.equal(popups.at(-1).removed, 1);
    const afterRemoval = popups.length;
    selection.select({lng: 1, lat: 1});
    assert.equal(popups.length, afterRemoval + 1);
    assert.equal(popups.at(-1).map, panels[0].map);
}

{
    const {panels, popups, selection} = harness(["baseline", "current"], "°C", sampleGrid);
    const interpolation = {latitudes: [0, 2], longitudes: [0, 4], values: [[0, 4], [8, 12]]};
    panels.forEach((panel, index) => selection.acceptData(panel, {
        interpolation: {...interpolation, values: interpolation.values.map(row => row.map(value => value + index * 3))},
        features: [feature({west: 0, east: 4, south: 0, north: 2, value: 999, latitude: 1, longitude: 2})],
    }));
    selection.select({lng: 1, lat: 0.5});
    assert.match(popups.at(-2).text(), /3 °C/);
    assert.match(popups.at(-1).text(), /6 °C/);
    assert.match(popups.at(-1).text(), /\+3 °C/);
    assert.match(popups.at(-1).text(), /Interpolated estimate from NOAA source-grid values/);
    assert.match(popups.at(-1).text(), /Estimate-based difference/);
    assert.doesNotMatch(popups.at(-1).text(), /Grid center|999 °C|Direct PostgreSQL/);
    selection.acceptData(panels[0], {interpolation: {...interpolation, values: [[null, 4], [8, 12]]}});
    assert.match(popups.at(-1).text(), /Baseline has no saved climate value/);
    selection.beginLoading(panels[1]);
    assert.match(popups.at(-1).text(), /This month is still loading/);
    assert.doesNotMatch(popups.at(-1).text(), /\+3 °C/);
}

console.log("Map selection readouts passed for one/four panels, values, states, safe text, and cleanup.");
