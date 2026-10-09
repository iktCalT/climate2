(() => {
    "use strict";
    const root = document.getElementById("location-fetch");
    if (!root) return;
    const label = document.getElementById("location-fetch-status");
    const retry = document.getElementById("location-fetch-retry");
    const latitude = Number(root.dataset.latitude);
    const longitude = Number(root.dataset.longitude);
    const query = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) });
    const controller = new AbortController();
    let stopped = false;
    let timer = null;
    let inFlight = false;
    const initialComplete = Number(root.dataset.completeMonths);
    let observedComplete = Number.isFinite(initialComplete) ? initialComplete : null;

    window.addEventListener("pagehide", () => {
        stopped = true;
        if (timer) clearTimeout(timer);
        controller.abort();
    }, { once: true });

    async function json(url, options) {
        const response = await fetch(url, {
            credentials: "same-origin", cache: "no-store", signal: controller.signal,
            ...options,
        });
        if (!response.ok) throw new Error("Location request failed");
        return response.json();
    }

    async function refreshSaved() {
        const response = await fetch(window.location.pathname + window.location.search, {
            credentials: "same-origin", cache: "no-store", signal: controller.signal,
        });
        if (!response.ok) throw new Error("Saved chart refresh failed");
        const next = new DOMParser().parseFromString(await response.text(), "text/html");
        const currentResult = document.querySelector(".location-result");
        const nextResult = next.querySelector(".location-result");
        if (!currentResult || !nextResult) throw new Error("Saved chart is unavailable");
        currentResult.replaceWith(nextResult);
        const selector = ".concise-locations > iframe, .concise-locations > .alert";
        const currentChart = document.querySelector(selector);
        const nextChart = next.querySelector(selector);
        if (currentChart && nextChart) currentChart.replaceWith(nextChart);
    }

    async function refreshIfAdvanced(state) {
        const complete = Number(state.complete);
        if (!Number.isFinite(complete)) return;
        if (observedComplete === null) {
            observedComplete = complete;
        } else if (complete > observedComplete) {
            await refreshSaved();
            observedComplete = complete;
        }
    }

    function message(state) {
        const progress = `${state.complete} of ${state.total} completed months saved; ${state.remaining} remain.`;
        if (state.state === "running") return `${progress} Downloading ${state.month}; a month can take several minutes.`;
        if (state.state === "done") return `All ${state.total} completed months are saved for this sample.`;
        if (state.state === "complete") return `${progress} The latest month was saved. Retry to continue when NOAA is available.`;
        if (state.state === "throttled") return `${progress} Hourly download allowance reached. Try again in about ${Math.ceil(state.retry_seconds / 60)} minutes.`;
        if (state.state === "busy") return `${progress} Another NOAA job is running. Try again later.`;
        if (state.state === "failed") return `${progress} Download failed. Saved values remain; retry when ready.`;
        if (state.state === "interrupted") return `${progress} The previous download was interrupted. Retry when ready.`;
        if (state.state === "disabled") return `${progress} Automatic fetching is disabled by the operator.`;
        return `${progress} Preparing the next missing month…`;
    }

    async function start() {
        return json("/api/location-fetch/start", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ latitude, longitude }),
        });
    }

    async function cycle(tryStart = false) {
        if (stopped || inFlight) return;
        inFlight = true;
        try {
            let state = tryStart ? await start() : await json(`/api/location-fetch/status?${query}`);
            if (stopped) return;
            await refreshIfAdvanced(state);
            if (state.state === "complete") {
                state = await start();
            } else if (state.state === "ready") {
                state = await start();
            }
            if (stopped) return;
            await refreshIfAdvanced(state);
            if (stopped) return;
            label.textContent = message(state);
            const waiting = state.state === "running";
            retry.hidden = waiting || state.state === "done" || state.state === "disabled";
            if (waiting) timer = setTimeout(() => cycle(), 3000);
        } catch (error) {
            if (stopped || error.name === "AbortError") return;
            label.textContent = "Location download status is unavailable. Saved values remain visible; retry when ready.";
            retry.hidden = false;
        } finally {
            inFlight = false;
        }
    }

    retry.addEventListener("click", () => cycle(true));
    cycle();
})();
