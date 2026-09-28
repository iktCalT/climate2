import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const source = await readFile(new URL("../static/map_selection.js", import.meta.url), "utf8");
const {createMapSelection} = await import(
    `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);

function harness(months, unit = "°C") {
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
        text() { return this.content.children.map(child => child.textContent).join("\n"); }
    }
    return {panels, popups, selection: createMapSelection({panels, Popup, document, unit})};
}

function feature({west, east, south, north, value, latitude, longitude, source = "direct_cache"}) {
    return {type: "Feature", geometry: {type: "Polygon", coordinates: [[
        [west, south], [east, south], [east, north], [west, north], [west, south],
    ]]}, properties: {value, latitude, longitude, source}};
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
}

{
    const {panels, popups, selection} = harness(["1990-01", "1990-02", "1990-03", "1990-04"], "mm/month");
    const cellA = feature({west: 0, east: 2, south: 0, north: 2, value: -4, latitude: 1, longitude: 1});
    const cellB = feature({west: 0, east: 2, south: 0, north: 2, value: 0.25, latitude: 1, longitude: 1,
        source: "nearby_cache"});
    panels.forEach((panel, i) => selection.acceptData(panel, {features: [i === 1 ? cellB : cellA]}));
    selection.select({lng: 0.1, lat: 0.1});
    assert.equal(popups.length, 4);
    assert.ok(popups.every(popup => popup.lngLat.lng === 0.1 && popup.lngLat.lat === 0.1));
    assert.match(popups[0].text(), /-4 mm\/month/);
    assert.match(popups[0].text(), /Direct PostgreSQL observation/);
    assert.match(popups[1].text(), /0\.25 mm\/month/);
    assert.match(popups[1].text(), /Reused nearby PostgreSQL observation/);
    assert.match(popups[2].text(), /1990-03/);
    assert.equal(popups[4 - 1].map, panels[3].map);
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

console.log("Map selection readouts passed for one/four panels, values, states, safe text, and cleanup.");
