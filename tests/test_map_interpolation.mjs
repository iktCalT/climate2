import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {test} from "node:test";

const source = await readFile(new URL("../static/map_interpolation.js", import.meta.url), "utf8");
const {sampleGrid, colorForValue, mercatorLatitude, createInterpolatedRaster} = await import(
    `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
const grid = {latitudes: [0, 2], longitudes: [0, 4], values: [[0, 4], [8, 12]]};
const scale = {stops: [[0, "#000000"], [6, "#ff0000"], [12, "#ffffff"]]};
export function fakeCanvas() {
    const canvas = {getContext: () => ({
        createImageData: (width, height) => ({data: new Uint8ClampedArray(width * height * 4)}),
        putImageData: image => { canvas.pixels = image.data; },
    })};
    return canvas;
}

test("numeric four-corner bilinear interpolation precedes nonlinear color stops", () => {
    assert.equal(sampleGrid(grid, 1, 0.5), 3);
    assert.equal(sampleGrid(grid, 2, 1), 6);
    assert.deepEqual(colorForValue(sampleGrid(grid, 2, 1), scale.stops), [255, 0, 0, 255]);
    const colorFirst = [0, 1, 2].map(channel => Math.round(grid.values.flat().reduce(
        (sum, value) => sum + colorForValue(value, scale.stops)[channel], 0) / 4));
    assert.notDeepEqual(colorFirst, [255, 0, 0]);
    assert.deepEqual(colorForValue(-100, scale.stops), [0, 0, 0, 255]);
    assert.deepEqual(colorForValue(100, scale.stops), [255, 255, 255, 255]);
});

test("nodes and edges require only nonzero-weight nodes; holes never extrapolate", () => {
    const hole = {...grid, values: [[0, 4], [null, Infinity]]};
    assert.equal(sampleGrid(hole, 0, 0), 0);
    assert.equal(sampleGrid(hole, 4, 0), 4);
    assert.equal(sampleGrid(hole, 2, 0), 2);
    assert.equal(sampleGrid(hole, 2, 1), null);
    for (const node of [null, NaN, Infinity, -Infinity, "12", undefined]) {
        assert.equal(sampleGrid({...grid, values: [[0, 4], [8, node]]}, 2, 1), null);
    }
    for (const [longitude, latitude] of [[-0.001, 1], [4.001, 1], [2, -0.001], [2, 2.001], [NaN, 1], [2, Infinity]]) {
        assert.equal(sampleGrid(grid, longitude, latitude), null);
    }
    const seam = {latitudes: [-2, 0], longitudes: [-180, -176, 176, 180], values: [[1, 3, 3, 1], [1, 3, 3, 1]]};
    assert.equal(sampleGrid(seam, -180, -1), sampleGrid(seam, 180, -1));
    assert.equal(sampleGrid(seam, -179, -1), 1.5);
    assert.equal(sampleGrid(seam, 179, -1), 1.5);
    assert.equal(sampleGrid(seam, 181, -1), null);
});

test("raster samples Mercator pixel centers, caps size, uses opaque colors and transparent holes", () => {
    assert.equal(mercatorLatitude(0.5), 0);
    assert.ok(Math.abs(mercatorLatitude(0) - 85.05112878) < 1e-7);
    const highGrid = {latitudes: [0, 80], longitudes: [0, 4], values: [[0, 0], [80, 80]]};
    const highScale = {stops: [[0, "#000000"], [80, "#ffffff"]]};
    const bounds = {west: 0, east: 4, south: 0, north: 80};
    const raster = createInterpolatedRaster({grid: highGrid, bounds, scale: highScale, width: 1, height: 1, canvasFactory: fakeCanvas});
    const midLatitude = Math.atan(Math.sinh(Math.asinh(Math.tan(80 * Math.PI / 180)) / 2)) * 180 / Math.PI;
    assert.deepEqual([...raster.canvas.pixels], colorForValue(midLatitude, highScale.stops));
    assert.notDeepEqual([...raster.canvas.pixels], colorForValue(40, highScale.stops));
    assert.deepEqual(raster.coordinates, [[0, 80], [4, 80], [4, 0], [0, 0]]);
    const capped = createInterpolatedRaster({grid, bounds: {west: 0, east: 4, south: 0, north: 2}, scale, width: 900, height: 1000, canvasFactory: fakeCanvas});
    assert.equal(capped.canvas.width, 512);
    assert.equal(capped.canvas.height, 512);
    assert.ok(capped.canvas.pixels.every((value, index) => index % 4 !== 3 || value === 255));
    const missing = createInterpolatedRaster({grid: {...grid, values: [[null, 4], [8, 12]]}, bounds: {west: 0, east: 4, south: 0, north: 2}, scale, width: 3, height: 3, canvasFactory: fakeCanvas});
    assert.ok(missing.canvas.pixels.every(value => value === 0));
});
