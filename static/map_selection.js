// A selection is evaluated against each panel's accepted viewport response.
// No rendered-feature query or network request is needed for a click.
const SOURCE_LABELS = {
    direct_cache: "Direct PostgreSQL observation",
    nearby_cache: "Reused nearby PostgreSQL observation",
    display_estimate: "Display-only nearest estimate (no cached coverage; not queued)",
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

export function createMapSelection({panels, Popup, document, unit}) {
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
        for (const panel of panels) {
            const entry = state.get(panel);
            if (!entry) continue;
            const body = document.createElement("div");
            line(document, body, panel.month, true);
            line(document, body, `Selected: ${selected.lat.toFixed(4)}° lat, ${selected.lng.toFixed(4)}° lon`);
            if (entry.phase === "loading") {
                line(document, body, "Loading viewport data…");
            } else if (entry.phase === "error") {
                line(document, body, "Map data unavailable for this viewport.");
            } else {
                const feature = containingCell(entry.data?.features, selected.lng, selected.lat);
                const value = feature?.properties?.value;
                if (typeof value !== "number" || !Number.isFinite(value)) {
                    line(document, body, "No saved climate data at this location.");
                } else {
                    line(document, body, `${value} ${unit}`, true);
                    line(document, body, SOURCE_LABELS[feature.properties.source] || "Source unavailable");
                    const centerLat = Number(feature.properties.latitude);
                    const centerLng = Number(feature.properties.longitude);
                    if (Number.isFinite(centerLat) && Number.isFinite(centerLng)) {
                        line(document, body, `Grid center: ${centerLat.toFixed(4)}° lat, ${centerLng.toFixed(4)}° lon`);
                    }
                }
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
