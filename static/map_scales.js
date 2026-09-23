const TEMPERATURE_COLORS = {
    coldest: "#053061",
    cold: "#2166ac",
    cool: "#67a9cf",
    neutral: "#f7f7f7",
    warm: "#fdae61",
    hot: "#d73027",
    hottest: "#67001f",
};

const PRECIPITATION_COLORS = {
    driest: "#f7fbff",
    light: "#deebf7",
    moderate: "#9ecae1",
    wet: "#6baed6",
    wetter: "#3182bd",
    heavy: "#08519c",
    heaviest: "#08306b",
};

export const SCALE_PRESETS = {
    temperature: {
        global: {
            id: "global",
            label: "Global extremes",
            min: -60,
            max: 60,
            unit: "°C",
            stops: [
                [-60, TEMPERATURE_COLORS.coldest],
                [-40, TEMPERATURE_COLORS.cold],
                [-20, TEMPERATURE_COLORS.cool],
                [0, TEMPERATURE_COLORS.neutral],
                [20, TEMPERATURE_COLORS.warm],
                [40, TEMPERATURE_COLORS.hot],
                [60, TEMPERATURE_COLORS.hottest],
            ],
        },
        temperate: {
            id: "temperate",
            label: "Temperate regional",
            min: -20,
            max: 40,
            unit: "°C",
            stops: [
                [-20, TEMPERATURE_COLORS.cold],
                [-10, TEMPERATURE_COLORS.cool],
                [0, "#d1e5f0"],
                [10, TEMPERATURE_COLORS.neutral],
                [20, "#fee090"],
                [30, TEMPERATURE_COLORS.warm],
                [40, TEMPERATURE_COLORS.hot],
            ],
        },
        cold: {
            id: "cold",
            label: "Cold regional",
            min: -50,
            max: 10,
            unit: "°C",
            stops: [
                [-50, TEMPERATURE_COLORS.coldest],
                [-40, TEMPERATURE_COLORS.cold],
                [-30, "#4393c3"],
                [-20, TEMPERATURE_COLORS.cool],
                [-10, "#d1e5f0"],
                [0, TEMPERATURE_COLORS.neutral],
                [10, TEMPERATURE_COLORS.warm],
            ],
        },
        warm: {
            id: "warm",
            label: "Warm regional",
            min: 0,
            max: 50,
            unit: "°C",
            stops: [
                [0, TEMPERATURE_COLORS.cold],
                [10, TEMPERATURE_COLORS.cool],
                [20, TEMPERATURE_COLORS.neutral],
                [30, "#fee090"],
                [40, TEMPERATURE_COLORS.warm],
                [45, TEMPERATURE_COLORS.hot],
                [50, TEMPERATURE_COLORS.hottest],
            ],
        },
    },
    precipitation: {
        global: {
            id: "global",
            label: "Global daily mean",
            min: 0,
            max: 20,
            unit: "mm/day",
            stops: [
                [0, PRECIPITATION_COLORS.driest],
                [1, PRECIPITATION_COLORS.light],
                [3, PRECIPITATION_COLORS.moderate],
                [6, PRECIPITATION_COLORS.wet],
                [10, PRECIPITATION_COLORS.wetter],
                [15, PRECIPITATION_COLORS.heavy],
                [20, PRECIPITATION_COLORS.heaviest],
            ],
        },
        dry: {
            id: "dry",
            label: "Dry-climate detail",
            min: 0,
            max: 5,
            unit: "mm/day",
            stops: [
                [0, PRECIPITATION_COLORS.driest],
                [0.25, PRECIPITATION_COLORS.light],
                [0.5, "#c6dbef"],
                [1, PRECIPITATION_COLORS.moderate],
                [2, PRECIPITATION_COLORS.wet],
                [3.5, PRECIPITATION_COLORS.wetter],
                [5, PRECIPITATION_COLORS.heavy],
            ],
        },
        wet: {
            id: "wet",
            label: "Wet-climate detail",
            min: 0,
            max: 50,
            unit: "mm/day",
            stops: [
                [0, PRECIPITATION_COLORS.driest],
                [2, PRECIPITATION_COLORS.light],
                [5, PRECIPITATION_COLORS.moderate],
                [10, PRECIPITATION_COLORS.wet],
                [20, PRECIPITATION_COLORS.wetter],
                [35, PRECIPITATION_COLORS.heavy],
                [50, PRECIPITATION_COLORS.heaviest],
            ],
        },
    },
};

const CUSTOM_LIMITS = {
    temperature: {min: -100, max: 80},
    precipitation: {min: 0, max: 500},
};
const HEX_COLOR = /^#[0-9a-f]{6}$/i;

export function scaleFamily(climateType) {
    return climateType === "precip" ? "precipitation" : "temperature";
}

export function presetScale(family, id = "global") {
    return SCALE_PRESETS[family]?.[id] || SCALE_PRESETS[family].global;
}

export function createCustomScale(family, values) {
    const min = Number(values.min);
    const max = Number(values.max);
    const colors = [values.lowColor, values.midColor, values.highColor];
    const limits = CUSTOM_LIMITS[family];

    if (!limits || !Number.isFinite(min) || !Number.isFinite(max)) {
        throw new Error("Enter finite minimum and maximum values.");
    }
    if (min >= max) {
        throw new Error("The maximum must be greater than the minimum.");
    }
    if (min < limits.min || max > limits.max) {
        throw new Error(
            family === "temperature"
                ? "Temperature bounds must stay between -100 and 80 °C."
                : "Precipitation bounds must stay between 0 and 500 mm/day."
        );
    }
    if (!colors.every((color) => HEX_COLOR.test(color))) {
        throw new Error("Choose valid six-digit colors for all three stops.");
    }

    const midpoint = min + (max - min) / 2;
    return {
        id: "custom",
        label: "Custom",
        min,
        max,
        unit: presetScale(family).unit,
        colors,
        stops: [
            [min, colors[0]],
            [midpoint, colors[1]],
            [max, colors[2]],
        ],
    };
}

export function customScaleFromScale(family, scale) {
    const middle = scale.stops[Math.floor(scale.stops.length / 2)];
    return createCustomScale(family, {
        min: scale.min,
        max: scale.max,
        lowColor: scale.stops[0][1],
        midColor: middle[1],
        highColor: scale.stops[scale.stops.length - 1][1],
    });
}

export function colorExpression(scale) {
    return [
        "interpolate",
        ["linear"],
        ["get", "value"],
        ...scale.stops.flat(),
    ];
}

export function storageKey(family) {
    return `climate2.mapScale.${family}`;
}

export function loadScale(family, storage) {
    try {
        const scaleStorage = storage || window.localStorage;
        const saved = JSON.parse(scaleStorage.getItem(storageKey(family)));
        if (!saved) {
            return presetScale(family);
        }
        if (saved.id === "custom") {
            return createCustomScale(family, saved);
        }
        return presetScale(family, saved.id);
    } catch (error) {
        return presetScale(family);
    }
}

export function saveScale(family, scale, storage) {
    try {
        const scaleStorage = storage || window.localStorage;
        const value = scale.id === "custom"
            ? {
                id: scale.id,
                min: scale.min,
                max: scale.max,
                lowColor: scale.colors[0],
                midColor: scale.colors[1],
                highColor: scale.colors[2],
            }
            : {id: scale.id};
        scaleStorage.setItem(storageKey(family), JSON.stringify(value));
    } catch (error) {
        // Rendering still works when private browsing blocks local storage.
    }
}
