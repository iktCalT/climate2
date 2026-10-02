import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

const profileSource = (await readFile(new URL("../static/community_profile.js", import.meta.url), "utf8")).replace("export function", "function");
const pinsSource = (await readFile(new URL("../static/community_pins.js", import.meta.url), "utf8")).replace(/^import .*\n/, "").replace("export function", "function");
const profileTemplate = await readFile(new URL("../templates/community_profile.html", import.meta.url), "utf8");
const pinsTemplate = await readFile(new URL("../templates/community_maps.html", import.meta.url), "utf8");

function element(tag = "div") {
    return {tag, listeners: {}, children: [], hidden: false, checked: false, value: "", textContent: "", dataset: {},
        addEventListener(name, callback) { this.listeners[name] = callback; },
        append(...children) { this.children.push(...children); },
        replaceChildren(...children) { this.children = children; },
        setAttribute(name, value) { this[name] = value; },
        reportValidity() { return this.valid !== false; },
        async fire(name) { return this.listeners[name]?.({preventDefault() {}, stopPropagation() {}}); },
        set innerHTML(_) { throw new Error("Untrusted HTML must never be rendered"); },
    };
}
function harness({denied = false, enabled = true, panels = []} = {}) {
    const elements = new Map();
    for (const id of [...profileTemplate.matchAll(/id="([^"]+)"/g), ...pinsTemplate.matchAll(/id="([^"]+)"/g)]) elements.set("#" + id[1], element());
    elements.get("#community-controls").dataset.enabled = String(enabled);
    const root = {querySelector: id => elements.get(id) || null};
    const operations = [], requests = [], markers = [], popups = [], timers = new Map();
    let saved = null, randomCalls = 0, serial = 0;
    const storage = {getItem() { operations.push("read"); if (denied) throw Error(); return saved; },
        setItem(_, value) { operations.push("write"); if (denied) throw Error(); saved = value; },
        removeItem() { operations.push("remove"); if (denied) throw Error(); saved = null; }};
    const crypto = {getRandomValues(bytes) { randomCalls++; assert.equal(bytes.length, 32); bytes.fill(171); return bytes; }};
    const fetch = (path, options) => new Promise(resolve => requests.push({path, options, resolve: data => resolve({ok: true, json: async () => data})}));
    class Marker { constructor({element}) { this.element = element; markers.push(this); } setLngLat(value) {this.coordinates = value; return this;} addTo() {return this;} remove() {this.removed = true;} }
    class Popup { constructor() {popups.push(this);} setLngLat() {return this;} setDOMContent(content) {this.content = content; return this;} addTo() {return this;} remove() {this.removed = true;} }
    const make = new Function("localStorage", "crypto", "document", "fetch", "setTimeout", "clearTimeout", "queueMicrotask", profileSource + "\n" + pinsSource + "\nreturn {createLocalProfile, createCommunityPins};");
    const functions = make(storage, crypto, {createElement: element}, fetch,
        callback => {timers.set(++serial, callback); return serial;}, id => timers.delete(id), callback => callback());
    return {root, elements, operations, requests, markers, popups, timers, panels, Marker, Popup, functions,
        randomCalls: () => randomCalls, saved: () => saved,
        pins() {return functions.createCommunityPins({root, panels, Marker, Popup});}};
}
async function activate(h) {
    await h.elements.get("#community-profile-open").fire("click");
    h.elements.get("#community-nickname").value = "Reader";
    h.elements.get("#community-storage-consent").checked = true;
    await h.elements.get("#community-profile-form").fire("submit");
}
const flush = () => new Promise(resolve => setImmediate(resolve));
function panel() {
    return {styleReady: true, map: {listeners: {}, on(name, callback) {this.listeners[name] = callback;},
        getBounds: () => ({getSouth: () => -85, getNorth: () => 85, getWest: () => -180, getEast: () => 180})}};
}

test("profile access and strong random identity require explicit consent; forgetting makes no request", async () => {
    const h = harness();
    const profile = h.functions.createLocalProfile({root: h.root});
    assert.deepEqual(h.operations, []);
    assert.equal(profile.get(), null);
    h.elements.get("#community-nickname").value = "Reader";
    await h.elements.get("#community-profile-form").fire("submit");
    assert.deepEqual(h.operations, []);
    assert.equal(h.randomCalls(), 0);
    await activate(h);
    assert.equal(h.randomCalls(), 1);
    assert.match(profile.get().token, /^[0-9a-f]{64}$/);
    assert.equal(JSON.parse(h.saved()).consent, true);
    await h.elements.get("#community-profile-forget").fire("click");
    assert.equal(profile.get(), null);
    assert.equal(h.saved(), null);
    assert.equal(h.requests.length, 0);
    assert.match(h.elements.get("#community-profile-status").textContent, /public pins remain/);
});

test("denied storage cannot activate an alternative identity or publish", async () => {
    const h = harness({denied: true});
    h.pins();
    assert.deepEqual(h.operations, []);
    await activate(h);
    assert.equal(h.elements.get("#community-publish").disabled, true);
    h.elements.get("#community-placement").checked = true;
    await h.elements.get("#community-pin-form").fire("submit");
    assert.equal(h.requests.length, 0);
    assert.match(h.elements.get("#community-profile-status").textContent, /no alternative identity was created/i);
});

test("ordinary clicks preserve readout flow; placement alone never publishes; native consent gates submit", async () => {
    const h = harness();
    const pins = h.pins();
    const click = {lngLat: {lat: 12, lng: 34}};
    assert.equal(pins.handleMapClick(click), false);
    await activate(h);
    h.elements.get("#community-placement").checked = true;
    assert.equal(pins.handleMapClick(click), true);
    assert.equal(h.elements.get("#community-latitude").value, 12);
    assert.equal(h.requests.length, 0);
    assert.match(pinsTemplate, /id="community-public-consent"[^>]*required/);
    const form = h.elements.get("#community-pin-form");
    form.valid = false; // Native reportValidity rejects unchecked required consent.
    await form.fire("submit");
    assert.equal(h.requests.length, 0);
    form.valid = true;
    h.elements.get("#community-comment").value = "Comment";
    h.elements.get("#community-public-consent").checked = true;
    const pending = form.fire("submit");
    assert.equal(h.requests.length, 1);
    assert.equal(h.requests[0].options.method, "POST");
    assert.match(h.requests[0].options.headers["X-Community-Token"], /^[0-9a-f]{64}$/);
    assert.deepEqual(JSON.parse(h.requests[0].options.body), {nickname: "Reader", comment: "Comment", latitude: 12, longitude: 34});
    h.requests[0].resolve({pin: {id: 1}});
    await pending;
    assert.equal(h.elements.get("#community-placement").checked, false);
    assert.equal(h.elements.get("#community-public-consent").checked, false);
});

test("public reads omit identity and render comments as text; pagination is explicit", async () => {
    const p = panel(), h = harness({panels: [p]});
    h.pins();
    const pending = h.elements.get("#community-retry").fire("click");
    assert.equal(h.operations.length, 0);
    assert.equal(h.requests[0].options.headers, undefined);
    assert.match(h.requests[0].path, /limit=100&cursor=0/);
    h.requests[0].resolve({pins: [{id: 1, nickname: "<img>", comment: "<script>alert(1)</script>", latitude: 1, longitude: 2}], more: true, next_cursor: 1});
    await pending;
    assert.equal(h.requests.length, 1);
    assert.equal(h.elements.get("#community-more").hidden, false);
    await h.markers[0].element.fire("click");
    assert.equal(h.popups[0].content.children[0].textContent, "<img>");
    assert.equal(h.popups[0].content.children[1].textContent, "<script>alert(1)</script>");
    const more = h.elements.get("#community-more").fire("click");
    assert.match(h.requests[1].path, /cursor=1/);
    h.requests[1].resolve({pins: [], more: false, next_cursor: null});
    await more;
    assert.equal(h.elements.get("#community-more").hidden, true);
});

test("movement and removal discard stale reads, markers and popups", async () => {
    const p = panel(), h = harness({panels: [p]});
    h.pins();
    const pending = h.elements.get("#community-retry").fire("click");
    p.map.listeners.move();
    assert.equal(h.requests[0].options.signal.aborted, true);
    h.requests[0].resolve({pins: [{id: 1, nickname: "old", comment: "old"}], more: false, next_cursor: null});
    await pending;
    assert.equal(h.markers.length, 0);
    const current = h.elements.get("#community-retry").fire("click");
    h.requests[1].resolve({pins: [{id: 2, nickname: "new", comment: "new", latitude: 1, longitude: 2}], more: false, next_cursor: null});
    await current;
    await h.markers[0].element.fire("click");
    p.map.listeners.remove();
    assert.equal(h.markers[0].removed, true);
    assert.equal(h.popups[0].removed, true);
    await h.elements.get("#community-retry").fire("click");
    await flush();
    assert.equal(h.requests.length, 2);
});
