// A selection is evaluated against each panel's accepted viewport response.
// No rendered-feature query or network request is needed for a click.
const SOURCE_LABELS = {
    direct_cache: "Direct PostgreSQL value",
    nearby_cache: "Reused nearby PostgreSQL value",
    display_estimate: "Display-only nearest estimate (no cached coverage; not queued)",
    interpolated_estimate: "Interpolated estimate from NOAA source-grid values",
};

function containingCell(features, longitude, latitude) {
    for (const feature of features || []) {
        const ring = feature?.geometry?.coordinates?.[0];
        if (feature?.geometry?.type !== "Polygon" || !Array.isArray(ring) || ring.length < 4) {
            continue;
        }
        const corners = ring.slice(0, 4);
        const west = Math.min(...corners.map(point => point[0]));
        const east = Math.max(...corners.map(point => point[0]));
        const south = Math.min(...corners.map(point => point[1]));
        const north = Math.max(...corners.map(point => point[1]));
        if (longitude >= west && longitude <= east && latitude >= south && latitude <= north) {
            return feature;
        }
    }
    return null;
}

function line(document, parent, content, strong = false) {
    const element = document.createElement(strong ? "strong" : "div");
    element.textContent = content;
    parent.append(element);
}

function displayValue(value) {
    const rounded = Number(value.toFixed(2));
    return String(rounded === 0 ? 0 : rounded);
}

function panelValue(entry, selected, sample) {
    if (!entry) return {status: "removed"};
    if (entry.phase === "loading") return {status: "loading"};
    if (entry.phase === "error") return {status: "error"};
    if (sample) {
        const value = sample(entry.data?.interpolation, selected.lng, selected.lat);
        return Number.isFinite(value)
            ? {status: "ready", value, source: "interpolated_estimate", feature: null}
            : {status: "missing"};
    }
    const feature = containingCell(entry.data?.features, selected.lng, selected.lat);
    const value = feature?.properties?.value;
    if (typeof value !== "number" || !Number.isFinite(value)) return {status: "missing"};
    return {status: "ready", value, source: feature.properties.source, feature};
}

function unavailableReason(value, label) {
    if (value.status === "removed") return `${label} panel is no longer available.`;
    if (value.status === "loading") return `${label} is still loading.`;
    if (value.status === "error") return `${label} map data is unavailable for this viewport.`;
    if (value.status === "missing") return `${label} has no saved climate value at this location.`;
    return "";
}

export function createMapSelection({panels, Popup, document, unit, sample}) {
    let selected = null;
    let suppressClose = false;
    const state = new Map(panels.map(panel => [panel, {
        phase: "loading", data: null, popup: null,
    }]));

    function discardPopups() {
        suppressClose = true;
        try {
            for (const entry of state.values()) {
                const popup = entry.popup;
                entry.popup = null;
                popup?.remove();
            }
        } finally {
            suppressClose = false;
        }
    }

    function clear() {
        selected = null;
        discardPopups();
    }

    function render() {
        discardPopups();
        if (!selected) return;
        const values = panels.map(panel => panelValue(state.get(panel), selected, sample));
        const comparing = panels.filter(panel => state.has(panel)).length > 1;
        const baseline = values[0];
        for (const panel of panels) {
            const entry = state.get(panel);
            if (!entry) continue;
            const index = panels.indexOf(panel);
            const value = values[index];
            const body = document.createElement("div");
            line(document, body, panel.month, true);
            if (comparing && index === 0) line(document, body, "Baseline", true);
            line(document, body, `Selected: ${selected.lat.toFixed(4)}° lat, ${selected.lng.toFixed(4)}° lon`);
            if (value.status === "loading") {
                line(document, body, "Loading viewport data…");
            } else if (value.status === "error") {
                line(document, body, "Map data unavailable for this viewport.");
            } else {
                if (value.status === "missing") {
                    line(document, body, "No saved climate data at this location.");
                } else {
                    line(document, body, `${displayValue(value.value)} ${unit}`, true);
                    line(document, body, SOURCE_LABELS[value.source] || "Source unavailable");
                    const centerLat = Number(value.feature?.properties?.latitude);
                    const centerLng = Number(value.feature?.properties?.longitude);
                    if (value.source !== "interpolated_estimate" && Number.isFinite(centerLat) && Number.isFinite(centerLng)) {
                        line(document, body, `Grid center: ${centerLat.toFixed(4)}° lat, ${centerLng.toFixed(4)}° lon`);
                    }
                }
            }
            if (comparing && index > 0) {
                const section = document.createElement("div");
                line(document, section, "Difference from baseline", true);
                const baselineReason = unavailableReason(baseline, "Baseline");
                const currentReason = unavailableReason(value, "This month");
                if (baselineReason || currentReason) {
                    line(document, section, baselineReason || currentReason);
                    if (baselineReason && currentReason) line(document, section, currentReason);
                } else {
                    const difference = value.value - baseline.value;
                    if (!Number.isFinite(difference)) {
                        line(document, section, "Difference unavailable because the numeric result is outside the supported range.");
                    } else {
                        const displayedDifference = Number(difference.toFixed(2));
                        const sign = displayedDifference > 0 ? "+" : displayedDifference < 0 ? "−" : "";
                        line(document, section, `${sign}${displayValue(Math.abs(displayedDifference))} ${unit}`, true);
                        if (baseline.source === "display_estimate" || value.source === "display_estimate"
                            || baseline.source === "interpolated_estimate" || value.source === "interpolated_estimate") {
                            line(document, section, "Estimate-based difference");
                        }
                    }
                }
                body.append(section);
            }
            if (Number.isFinite(selected.lat) && selected.lat >= -90 && selected.lat <= 90
                && Number.isFinite(selected.lng) && selected.lng >= -180 && selected.lng <= 180) {
                const historyLink = document.createElement("a");
                const query = new URLSearchParams({
                    latitude: String(selected.lat),
                    longitude: String(selected.lng),
                });
                historyLink.href = `/locations?${query.toString()}`;
                historyLink.textContent = "View saved location history";
                body.append(historyLink);
                line(document, body, "History uses its own sampling rule and may differ from the map display estimate.");
            }
            const popup = new Popup({closeOnClick: false})
                .setLngLat(selected)
                .setDOMContent(body)
                .addTo(panel.map);
            entry.popup = popup;
            popup.on("close", () => {
                if (!suppressClose && entry.popup === popup) clear();
            });
        }
    }

    return {
        select(lngLat) {
            const lng = Number(lngLat?.lng);
            const lat = Number(lngLat?.lat);
            if (!Number.isFinite(lng) || !Number.isFinite(lat)) return;
            selected = {lng, lat};
            render();
        },
        beginLoading(panel) {
            const entry = state.get(panel);
            if (!entry) return;
            entry.phase = "loading";
            entry.data = null;
            if (selected) render();
        },
        acceptData(panel, data) {
            const entry = state.get(panel);
            if (!entry) return;
            entry.phase = "ready";
            entry.data = data;
            if (selected) render();
        },
        fail(panel) {
            const entry = state.get(panel);
            if (!entry) return;
            entry.phase = "error";
            entry.data = null;
            if (selected) render();
        },
        clear,
        removePanel(panel) {
            clear();
            state.delete(panel);
        },
    };
}
