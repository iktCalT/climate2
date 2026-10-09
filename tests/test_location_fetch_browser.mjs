import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../static/location_fetch.js", import.meta.url), "utf8");
const tick = () => new Promise(resolve => setImmediate(resolve));

function harness(initialComplete = 1) {
    const requests = [], timers = new Map(), events = {}, replacements = [];
    let nextTimer = 0, storageReads = 0;
    const root = {dataset: {latitude: "1", longitude: "-2", completeMonths: String(initialComplete)}};
    const label = {textContent: ""};
    const retry = {hidden: true, addEventListener(name, callback) { this[name] = callback; }};
    const currentResult = {replaceWith(next) { replacements.push(["result", next]); }};
    const currentChart = {replaceWith(next) { replacements.push(["chart", next]); }};
    const nextResult = {kind: "next result"}, nextChart = {kind: "next chart"};
    const document = {
        getElementById(id) { return ({"location-fetch": root, "location-fetch-status": label,
            "location-fetch-retry": retry})[id]; },
        querySelector(selector) { return selector === ".location-result" ? currentResult : currentChart; },
    };
    const window = {location: {pathname: "/locations", search: "?latitude=1&longitude=-2"},
        addEventListener(name, callback) { events[name] = callback; }};
    class DOMParser {
        parseFromString() {
            return {querySelector(selector) { return selector === ".location-result" ? nextResult : nextChart; }};
        }
    }
    const fetch = (path, options) => new Promise(resolve => {
        requests.push({path, options, respond(data, ok = true) {
            resolve({ok, json: async () => data, text: async () => data});
        }});
    });
    const sandbox = {document, window, DOMParser, fetch, AbortController, URLSearchParams,
        setTimeout(callback) { const id = ++nextTimer; timers.set(id, callback); return id; },
        clearTimeout(id) { timers.delete(id); }};
    Object.defineProperty(sandbox, "localStorage", {get() { storageReads++; throw Error("storage accessed"); }});
    vm.runInNewContext(source, sandbox);
    return {requests, timers, events, replacements, label, retry, storageReads: () => storageReads,
        async respond(index, data, ok = true) { requests[index].respond(data, ok); await tick(); },
        async poll() { const [id, callback] = timers.entries().next().value; timers.delete(id); callback(); await tick(); },
        async click() { retry.click(); await tick(); }};
}

const state = (name, changes = {}) => ({state: name, complete: 1, total: 3, remaining: 2,
    month: "2026-08", retry_seconds: 0, ...changes});

test("initial status starts one missing month and schedules polling without storage", async () => {
    const h = harness();
    assert.match(h.requests[0].path, /^\/api\/location-fetch\/status\?/);
    assert.equal(h.requests[0].options.credentials, "same-origin");
    await h.respond(0, state("ready"));
    assert.equal(h.requests[1].path, "/api/location-fetch/start");
    assert.deepEqual(JSON.parse(h.requests[1].options.body), {latitude: 1, longitude: -2});
    assert.equal(h.requests[1].options.headers["Content-Type"], "application/json");
    await h.respond(1, state("running"));
    assert.match(h.label.textContent, /1 of 3.*Downloading 2026-08/);
    assert.equal(h.retry.hidden, true);
    assert.equal(h.timers.size, 1);
    assert.equal(h.storageReads(), 0);
});

test("completed month refreshes saved result then starts next; final done refreshes and stops", async () => {
    const h = harness();
    await h.respond(0, state("running"));
    await h.poll();
    await h.respond(1, state("complete", {complete: 2, remaining: 1}));
    assert.equal(h.requests[2].path, "/locations?latitude=1&longitude=-2");
    await h.respond(2, "<html></html>");
    assert.deepEqual(h.replacements.map(([name]) => name), ["result", "chart"]);
    assert.equal(h.requests[3].path, "/api/location-fetch/start");
    await h.respond(3, state("running", {complete: 2, remaining: 1, month: "1951-01"}));
    assert.match(h.label.textContent, /2 of 3.*1951-01/);
    await h.poll();
    await h.respond(4, state("done", {complete: 3, remaining: 0}));
    assert.equal(h.requests[5].path, "/locations?latitude=1&longitude=-2");
    await h.respond(5, "<html></html>");
    assert.match(h.label.textContent, /All 3 completed months/);
    assert.equal(h.timers.size, 0);
    assert.equal(h.retry.hidden, true);
    assert.equal(h.storageReads(), 0);
});

test("failed response and throttling stop polling, expose retry, and retain saved view", async () => {
    for (const response of [state("failed"), state("throttled", {retry_seconds: 121})]) {
        const h = harness();
        await h.respond(0, response);
        assert.equal(h.timers.size, 0);
        assert.equal(h.retry.hidden, false);
        assert.equal(h.replacements.length, 0);
        assert.match(h.label.textContent, response.state === "failed" ? /Download failed/ : /about 3 minutes/);
        await h.click();
        assert.equal(h.requests[1].path, "/api/location-fetch/start");
    }
});

test("request errors permit explicit retry; pagehide cancels timer and aborts in-flight work", async () => {
    const error = harness();
    await error.respond(0, {}, false);
    assert.match(error.label.textContent, /status is unavailable/);
    assert.equal(error.retry.hidden, false);
    await error.click();
    assert.equal(error.requests[1].path, "/api/location-fetch/start");

    const h = harness();
    await h.respond(0, state("running"));
    assert.equal(h.timers.size, 1);
    h.events.pagehide();
    assert.equal(h.timers.size, 0);
    assert.equal(h.requests[0].options.signal.aborted, true);
    await h.click();
    assert.equal(h.requests.length, 1);
    assert.equal(h.storageReads(), 0);
});

test("another sample replacing the singleton job still refreshes newly saved coverage", async () => {
    const h = harness(1);
    await h.respond(0, state("running"));
    await h.poll();
    await h.respond(1, state("busy", {complete: 2, remaining: 1, month: null}));
    assert.equal(h.requests[2].path, "/locations?latitude=1&longitude=-2");
    await h.respond(2, "<html></html>");
    assert.deepEqual(h.replacements.map(([name]) => name), ["result", "chart"]);
    assert.equal(h.requests.length, 3);
    assert.equal(h.timers.size, 0);
    assert.equal(h.retry.hidden, false);
    assert.match(h.label.textContent, /2 of 3.*Another NOAA job/);
    assert.equal(h.storageReads(), 0);
});

test("ready and done count advances refresh once; unchanged counts do not reload", async () => {
    const ready = harness(1);
    await ready.respond(0, state("ready", {complete: 2, remaining: 1}));
    assert.equal(ready.requests[1].path, "/locations?latitude=1&longitude=-2");
    await ready.respond(1, "<html></html>");
    assert.equal(ready.requests[2].path, "/api/location-fetch/start");
    await ready.respond(2, state("running", {complete: 2, remaining: 1}));
    assert.equal(ready.replacements.length, 2);
    assert.equal(ready.requests.length, 3);

    const done = harness(2);
    await done.respond(0, state("done", {complete: 3, remaining: 0}));
    assert.equal(done.requests[1].path, "/locations?latitude=1&longitude=-2");
    await done.respond(1, "<html></html>");
    assert.equal(done.replacements.length, 2);
    assert.equal(done.timers.size, 0);
    const unchanged = harness(3);
    await unchanged.respond(0, state("done", {complete: 3, remaining: 0}));
    assert.equal(unchanged.requests.length, 1);
    assert.equal(unchanged.replacements.length, 0);
});
