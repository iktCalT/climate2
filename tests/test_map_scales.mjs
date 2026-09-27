import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const source = await readFile(new URL("../static/map_scales.js", import.meta.url), "utf8");
const {SCALE_PRESETS, loadScale, saveScale, colorExpression, createCustomScale} =
    await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
const values = new Map();
const storage = {getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value)};
assert.equal(loadScale("temperature", storage).id, "global");
for (const id of ["detail_cold", "detail_mild", "detail_warm"]) {
    const scale = SCALE_PRESETS.temperature[id];
    assert.equal(scale.max - scale.min, 20);
    assert.equal(scale.stops.length, 11);
    scale.stops.forEach(([value], index) => assert.equal(value, scale.min + index * 2));
    saveScale("temperature", scale, storage);
    assert.deepEqual(loadScale("temperature", storage), scale);
    assert.deepEqual(colorExpression(scale).slice(3), scale.stops.flat());
}
const custom = createCustomScale("temperature", {min: 4.5, max: 8.5,
    lowColor: "#053061", midColor: "#ffffff", highColor: "#67001f"});
saveScale("temperature", custom, storage);
assert.deepEqual(loadScale("temperature", storage), custom);
assert.equal(loadScale("precipitation", storage).id, "global");
assert.throws(() => createCustomScale("temperature", {min: 10, max: 10}));
console.log("Manual detail presets, saved selections, custom range, and shared color expressions passed.");
