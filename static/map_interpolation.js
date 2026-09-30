const MAX_RASTER_SIDE = 512;
const MERCATOR_LIMIT = 85.051129;

function bracket(axis, coordinate) {
    if (!Array.isArray(axis) || axis.length < 2 || coordinate < axis[0] || coordinate > axis.at(-1)) {
        return null;
    }
    let low = 1;
    let high = axis.length - 1;
    while (low < high) {
        const middle = Math.floor((low + high) / 2);
        if (axis[middle] < coordinate) low = middle + 1;
        else high = middle;
    }
    const upper = low;
    const lower = upper - 1;
    return [lower, upper, (coordinate - axis[lower]) / (axis[upper] - axis[lower])];
}

export function sampleGrid(grid, longitude, latitude) {
    const x = bracket(grid?.longitudes, longitude);
    const y = bracket(grid?.latitudes, latitude);
    if (!x || !y) return null;
    const [x0, x1, tx] = x;
    const [y0, y1, ty] = y;
    const corners = [
        [y0, x0, (1 - tx) * (1 - ty)],
        [y0, x1, tx * (1 - ty)],
        [y1, x0, (1 - tx) * ty],
        [y1, x1, tx * ty],
    ];
    let value = 0;
    for (const [row, column, weight] of corners) {
        if (weight === 0) continue;
        const node = grid.values?.[row]?.[column];
        if (typeof node !== "number" || !Number.isFinite(node)) return null;
        value += node * weight;
    }
    return Number.isFinite(value) ? value : null;
}

function colorChannels(color) {
    const match = /^#([\da-f]{6})$/i.exec(color || "");
    return match ? [0, 2, 4].map(index => Number.parseInt(match[1].slice(index, index + 2), 16)) : null;
}

export function colorForValue(value, stops) {
    if (!Number.isFinite(value) || !Array.isArray(stops) || stops.length < 2) return null;
    let right = stops.findIndex(([stop]) => stop >= value);
    if (right < 0) right = stops.length - 1;
    if (right === 0) right = 1;
    const [leftValue, leftColor] = stops[right - 1];
    const [rightValue, rightColor] = stops[right];
    const left = colorChannels(leftColor);
    const rightRgb = colorChannels(rightColor);
    if (!left || !rightRgb) return null;
    const ratio = Math.max(0, Math.min(1, (value - leftValue) / (rightValue - leftValue)));
    return [...left.map((channel, index) => Math.round(channel + ratio * (rightRgb[index] - channel))), 255];
}

export function mercatorLatitude(y) {
    return Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180 / Math.PI;
}

export function createInterpolatedRaster({grid, bounds, scale, width = 512, height = 512, canvasFactory = () => document.createElement("canvas")}) {
    const west = Math.max(-180, bounds.west);
    const east = Math.min(180, bounds.east);
    const northY = mercatorY(Math.min(MERCATOR_LIMIT, bounds.north));
    const southY = mercatorY(Math.max(-MERCATOR_LIMIT, bounds.south));
    width = Math.max(1, Math.min(MAX_RASTER_SIDE, Math.round(width)));
    height = Math.max(1, Math.min(MAX_RASTER_SIDE, Math.round(height)));
    const canvas = canvasFactory();
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d", {willReadFrequently: false});
    const image = context.createImageData(width, height);
    for (let py = 0; py < height; py += 1) {
        const y = northY + (py + 0.5) / height * (southY - northY);
        const latitude = mercatorLatitude(y);
        for (let px = 0; px < width; px += 1) {
            const longitude = west + (px + 0.5) / width * (east - west);
            const value = sampleGrid(grid, longitude, latitude);
            if (value === null) continue;
            const rgba = colorForValue(value, scale.stops);
            if (!rgba) continue;
            const offset = (py * width + px) * 4;
            image.data.set(rgba, offset);
        }
    }
    context.putImageData(image, 0, 0);
    return {canvas, coordinates: [[west, bounds.north], [east, bounds.north], [east, bounds.south], [west, bounds.south]]};
}

function mercatorY(latitude) {
    const radians = latitude * Math.PI / 180;
    return (1 - Math.asinh(Math.tan(radians)) / Math.PI) / 2;
}
