import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

const profileSource = (await readFile(new URL("../static/community_profile.js", import.meta.url), "utf8")).replace("export function", "function");
const pinsSource = (await readFile(new URL("../static/community_pins.js", import.meta.url), "utf8")).replace(/^import .*\n/, "").replace("export function", "function");
const profileTemplate = await readFile(new URL("../templates/community_profile.html", import.meta.url), "utf8");
const pinsTemplate = await readFile(new URL("../templates/community_maps.html", import.meta.url), "utf8");

function element(tag = "div") {
    return {tag, listeners: {}, children: [], hidden: false, checked: false, value: "", textContent: "", dataset: {}, focused: false,
        addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); },
        focus() { this.focused = true; },
        append(...children) { this.children.push(...children); },
        replaceChildren(...children) { this.children = children; },
        setAttribute(name, value) { this[name] = value; },
        setCustomValidity(message) { this.customValidityMessage = message; this.validity = {customError: Boolean(message)}; },
        reportValidity() { return this.reportValidityOverride ?? (this.valid !== false && !this.customValidityMessage); },
        async fire(name) { let result; for (const callback of this.listeners[name] || []) result = await callback({preventDefault() {}, stopPropagation() {}}); return result; },
        set innerHTML(_) { throw new Error("Untrusted HTML must never be rendered"); },
    };
}
function harness({denied = false, enabled = true, panels = [], confirmResult = true} = {}) {
    const elements = new Map();
    for (const id of [...profileTemplate.matchAll(/id="([^"]+)"/g), ...pinsTemplate.matchAll(/id="([^"]+)"/g)]) elements.set("#" + id[1], element());
    elements.get("#community-controls").dataset.enabled = String(enabled);
    const root = {querySelector: id => elements.get(id) || null};
    const operations = [], requests = [], markers = [], popups = [], timers = new Map(), confirmations = [];
    let saved = null, randomCalls = 0, serial = 0, removeDenied = false, clock = Date.now();
    const storage = {getItem() { operations.push("read"); if (denied) throw Error(); return saved; },
        setItem(_, value) { operations.push("write"); if (denied) throw Error(); saved = value; },
        removeItem() { operations.push("remove"); if (denied || removeDenied) throw Error(); saved = null; }};
    const crypto = {getRandomValues(bytes) { randomCalls++; assert.equal(bytes.length, 32); bytes.fill(171); return bytes; }};
    const fetch = (path, options) => new Promise(resolve => requests.push({path, options,
        resolve: (data, ok = true) => resolve({ok, json: async () => data})}));
    class Marker { constructor({element}) { this.element = element; markers.push(this); } setLngLat(value) {this.coordinates = value; return this;} addTo(map) {this.map = map; return this;} remove() {this.removed = true;} }
    const animationFrames = new Map(), observers = [];
    let frameSerial = 0;
    class ResizeObserverMock {
        constructor(callback) { this.callback = callback; this.targets = []; this.disconnected = false; observers.push(this); }
        observe(target) { this.targets.push(target); }
        disconnect() { this.disconnected = true; }
        trigger() { if (!this.disconnected) this.callback(); }
    }
    class Popup {
        constructor(options = {}) { this.options = options; this.listeners = {}; this.element = element("popup");
            this.element.style = {translate: "none", maxWidth: "", values: new Map(), setProperty(name, value) { this.values.set(name, value); }};
            this.element.classList = {values: new Set(), toggle(name, force) { if (force) this.values.add(name); else this.values.delete(name); }};
            this.baseRect = {left: 0, top: 0, width: 160, height: 80}; this.element.getBoundingClientRect = () => {
                const [x = 0, y = 0] = this.element.style.translate === "none" ? [] : this.element.style.translate.split("px").map(Number);
                const mapRect = this.map?.getContainer().getBoundingClientRect();
                const widthLimit = Number.parseFloat(this.element.style.maxWidth);
                const heightLimit = Number.parseFloat(this.element.style.values.get("--community-popup-height"));
                const width = Number.isFinite(widthLimit) ? Math.min(this.baseRect.width, widthLimit) : this.baseRect.width;
                const height = Number.isFinite(heightLimit) ? Math.min(this.baseRect.height, heightLimit) : this.baseRect.height;
                const left = this.baseRect.left + (Number.isFinite(x) ? x : 0);
                const top = this.baseRect.top + (Number.isFinite(y) ? y : 0);
                return {left, top, right: left + width, bottom: top + height, width, height};
            };
            popups.push(this);
        }
        setLngLat() {return this;}
        setDOMContent(content) {this.content = content; return this;}
        getElement() {return this.element;}
        on(name, callback) {(this.listeners[name] ||= []).push(callback); return this;}
        addTo(map) {this.map = map; return this;}
        remove() {if (this.removed) return; this.removed = true; for (const callback of this.listeners.close || []) callback();}
    }
    function TestDate(...args) { return new Date(...args); }
    TestDate.now = () => clock;
    TestDate.prototype = Date.prototype;
    const make = new Function("localStorage", "crypto", "document", "fetch", "setTimeout", "clearTimeout", "queueMicrotask", "confirm", "Date", "requestAnimationFrame", "cancelAnimationFrame", "ResizeObserver", profileSource + "\n" + pinsSource + "\nreturn {createLocalProfile, createCommunityPins};");
    const functions = make(storage, crypto, {createElement: element}, fetch,
        (callback, delay) => {timers.set(++serial, {callback, delay}); return serial;}, id => timers.delete(id), queueMicrotask,
        message => {confirmations.push(message); return confirmResult;}, TestDate,
        callback => { const id = ++frameSerial; animationFrames.set(id, callback); return id; }, id => animationFrames.delete(id), ResizeObserverMock);
    return {root, elements, operations, requests, markers, popups, timers, confirmations, panels, Marker, Popup, observers, animationFrames, functions,
        flushFrames() { const frames = [...animationFrames.entries()]; animationFrames.clear(); for (const [, callback] of frames) callback(); },
        randomCalls: () => randomCalls, saved: () => saved,
        now: () => clock,
        advance(ms) { clock += ms; },
        seed(value) { saved = JSON.stringify(value); },
        denyRemoval() {removeDenied = true;},
        pins() {return functions.createCommunityPins({root, panels, Marker, Popup});}};
}
async function activate(h) {
    await h.elements.get("#community-profile-open").fire("click");
    h.elements.get("#community-nickname").value = "Reader";
    h.elements.get("#community-storage-consent").checked = true;
    await h.elements.get("#community-profile-form").fire("submit");
}
const flush = () => new Promise(resolve => setImmediate(resolve));
function panel(styleReady = true) {
    const bounds = {left: 0, top: 0, width: 320, height: 240};
    return {styleReady, bounds, map: {listeners: {}, on(name, callback) {this.listeners[name] = callback;}, getContainer() {return {getBoundingClientRect: () => ({...bounds, right: bounds.left + bounds.width, bottom: bounds.top + bounds.height})};},
        getBounds: () => ({getSouth: () => -85, getNorth: () => 85, getWest: () => -180, getEast: () => 180})}};
}
const drafts = h => h.markers.filter(marker => marker.element.className === "community-draft-marker");

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
    assert.equal(h.confirmations.length, 1);
    assert.match(h.confirmations[0], /public pins will remain/i);
    assert.match(h.confirmations[0], /lose the credential/i);
    assert.equal(profile.get(), null);
    assert.equal(h.saved(), null);
    assert.equal(h.requests.length, 0);
    assert.match(h.elements.get("#community-profile-status").textContent, /public pins remain/);
});

test("cancelled native confirmation preserves saved bytes, active profile, controls and callbacks", async () => {
    const h = harness({confirmResult: false});
    const changes = [];
    const profile = h.functions.createLocalProfile({root: h.root, onChange: value => changes.push(value)});
    await activate(h);
    const saved = h.saved(), active = profile.get();
    const forget = h.elements.get("#community-profile-forget");
    const form = h.elements.get("#community-profile-form");
    const status = h.elements.get("#community-profile-status");
    const before = {operations: h.operations.slice(), requests: h.requests.length,
        forgetHidden: forget.hidden, formHidden: form.hidden, status: status.textContent,
        changes: changes.length};
    await forget.fire("click");
    assert.equal(h.confirmations.length, 1);
    assert.match(h.confirmations[0], /public pins will remain/i);
    assert.match(h.confirmations[0], /lose the credential/i);
    assert.equal(h.saved(), saved);
    assert.equal(profile.get(), active);
    assert.deepEqual(h.operations, before.operations);
    assert.equal(h.requests.length, before.requests);
    assert.equal(forget.hidden, before.forgetHidden);
    assert.equal(form.hidden, before.formHidden);
    assert.equal(status.textContent, before.status);
    assert.equal(changes.length, before.changes);
});

test("cancelled forget keeps pin publishing and own-pin controls active", async () => {
    const h = harness({confirmResult: false});
    h.pins();
    await activate(h);
    const publish = h.elements.get("#community-publish");
    const own = h.elements.get("#community-own-pins");
    assert.equal(publish.disabled, false);
    assert.equal(own.hidden, false);
    const saved = h.saved(), operations = h.operations.slice();
    await h.elements.get("#community-profile-forget").fire("click");
    assert.equal(h.confirmations.length, 1);
    assert.equal(h.saved(), saved);
    assert.deepEqual(h.operations, operations);
    assert.equal(publish.disabled, false);
    assert.equal(own.hidden, false);
    assert.equal(h.requests.length, 0);
});

test("confirmed forget updates controls once; failed removal leaves saved bytes and inactive error state", async () => {
    for (const fails of [false, true]) {
        const h = harness();
        const changes = [];
        const profile = h.functions.createLocalProfile({root: h.root, onChange: value => changes.push(value)});
        await activate(h);
        const saved = h.saved(), calls = changes.length;
        if (fails) h.denyRemoval();
        await h.elements.get("#community-profile-forget").fire("click");
        assert.equal(h.confirmations.length, 1);
        assert.equal(changes.length, calls + 1);
        assert.equal(changes.at(-1), null);
        assert.equal(profile.get(), null);
        assert.equal(h.elements.get("#community-profile-form").hidden, false);
        assert.equal(h.elements.get("#community-profile-forget").hidden, !fails);
        assert.equal(h.saved(), fails ? saved : null);
        assert.equal(h.operations.at(-1), "remove");
        assert.equal(h.requests.length, 0);
        assert.match(h.elements.get("#community-profile-status").textContent,
            fails ? /saved profile may remain on this device/i : /public pins remain/i);
    }
});

test("new profiles expire after a fixed 30 days and explicit reuse never slides the date", async () => {
    const h = harness();
    const profile = h.functions.createLocalProfile({root: h.root});
    await activate(h);
    const created = JSON.parse(h.saved());
    assert.equal(created.expiresAt, h.now() + 30 * 24 * 60 * 60 * 1000);
    await h.elements.get("#community-profile-open").fire("click");
    assert.equal(profile.get().token, created.token);
    assert.equal(JSON.parse(h.saved()).expiresAt, created.expiresAt);
    assert.equal(h.randomCalls(), 1);
    assert.deepEqual(h.operations.slice(-2), ["read", "write"]);
});

test("legacy reuse keeps its token, while malformed and expired records fail closed", async () => {
    const h = harness();
    const profile = h.functions.createLocalProfile({root: h.root});
    const legacy = {nickname: "Old", consent: true, token: "ab".repeat(32)};
    h.seed(legacy);
    await h.elements.get("#community-profile-open").fire("click");
    const upgraded = JSON.parse(h.saved());
    assert.equal(upgraded.token, legacy.token);
    assert.equal(upgraded.expiresAt, h.now() + 30 * 24 * 60 * 60 * 1000);
    assert.equal(profile.get().token, legacy.token);
    assert.equal(h.randomCalls(), 0);

    h.seed({...legacy, expiresAt: "not-a-date"});
    await h.elements.get("#community-profile-open").fire("click");
    assert.equal(profile.get(), null);
    assert.equal(h.randomCalls(), 0);
    assert.equal(h.requests.length, 0);
    assert.notEqual(h.saved(), null, "malformed expiry does not activate or silently delete the stored record");

    h.seed({...legacy, expiresAt: h.now() - 1});
    await h.elements.get("#community-profile-open").fire("click");
    assert.equal(profile.get(), null);
    assert.equal(h.saved(), null, "expired local data is removed only during explicit reuse");
    assert.ok(h.operations.includes("remove"));
});

test("failed explicit removal of an expired record stays inactive and reports storage failure", async () => {
    const h = harness();
    const profile = h.functions.createLocalProfile({root: h.root});
    h.seed({nickname: "Old", consent: true, token: "ab".repeat(32), expiresAt: h.now() - 1});
    h.denyRemoval();
    await h.elements.get("#community-profile-open").fire("click");
    assert.equal(profile.get(), null);
    assert.notEqual(h.saved(), null);
    assert.equal(h.operations.at(-1), "remove");
    assert.match(h.elements.get("#community-profile-status").textContent, /local storage is unavailable/i);
});

test("active expiry deactivates controls and blocks later publish and own-pin deletion without storage access", async () => {
    const h = harness();
    h.pins();
    await activate(h);
    const ownButton = h.elements.get("#community-own-refresh");
    const loading = ownButton.fire("click");
    assert.equal(h.requests.length, 1);
    h.requests[0].resolve({pins: [{id: 77, latitude: 1, longitude: 2, comment: ""}]});
    await loading;
    const detachedDelete = h.elements.get("#community-own-list").children[0].children[1];
    const identity = JSON.parse(h.saved());
    const shortExpiry = h.now() + 1000;
    h.seed({...JSON.parse(h.saved()), expiresAt: shortExpiry});
    await h.elements.get("#community-profile-open").fire("click");
    const activeTimers = [...h.timers.values()].filter(timer => timer.delay === 1000);
    assert.ok(activeTimers.length >= 1);
    const operationsBefore = h.operations.slice();
    h.advance(shortExpiry - h.now());
    for (const timer of activeTimers) timer.callback();
    assert.equal(h.elements.get("#community-publish").disabled, true);
    assert.equal(h.elements.get("#community-own-pins").hidden, true);
    assert.equal(h.elements.get("#community-own-list").children.length, 0);
    assert.deepEqual(h.operations, operationsBefore, "the expiry timer never reads, writes, or removes storage");

    h.elements.get("#community-placement").checked = true;
    h.elements.get("#community-public-consent").checked = true;
    await h.elements.get("#community-pin-form").fire("submit");
    await detachedDelete.fire("click");
    assert.equal(h.requests.length, 1, "expired publish and detached own-pin delete issue no request");
});

test("expired profile requires a fresh consent action before replacement identity creation", async () => {
    const h = harness();
    const profile = h.functions.createLocalProfile({root: h.root});
    await activate(h);
    const identity = profile.get();
    const shortExpiry = h.now() + 1000;
    h.seed({...JSON.parse(h.saved()), expiresAt: shortExpiry});
    await h.elements.get("#community-profile-open").fire("click");
    h.advance(shortExpiry - h.now());
    const timer = [...h.timers.values()].findLast(item => item.delay === 1000);
    assert.ok(timer);
    timer.callback();
    await h.elements.get("#community-profile-open").fire("click");
    assert.equal(h.elements.get("#community-storage-consent").checked, false);
    h.elements.get("#community-nickname").value = "Replacement";
    await h.elements.get("#community-profile-form").fire("submit");
    assert.equal(profile.get(), null);
    assert.equal(h.randomCalls(), 1, "no replacement token is minted without renewed consent");
});

test("long expiry timers rearm in bounded intervals without touching storage", async () => {
    const h = harness();
    const profile = h.functions.createLocalProfile({root: h.root});
    const expiresAt = h.now() + 60 * 24 * 60 * 60 * 1000;
    h.seed({nickname: "Reader", consent: true, token: "ab".repeat(32), expiresAt});
    await h.elements.get("#community-profile-open").fire("click");
    const timer = [...h.timers.values()].findLast(item => item.delay === 2_147_000_000);
    assert.ok(timer, "timeout is capped below the platform maximum");
    const before = h.operations.slice();
    h.advance(timer.delay);
    timer.callback();
    assert.equal(profile.get().expiresAt, expiresAt);
    assert.deepEqual(h.operations, before);
    assert.ok([...h.timers.values()].some(item => item.delay > 0 && item.delay <= 2_147_000_000));
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
    assert.equal(h.elements.get("#community-latitude").value, "12");
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

test("active identity can read and delete a message-free own pin", async () => {
    const h = harness();
    h.pins();
    await activate(h);
    const load = h.elements.get("#community-own-refresh").fire("click");
    assert.equal(h.requests[0].path, "/api/community/my-pins");
    assert.match(h.requests[0].options.headers["X-Community-Token"], /^[0-9a-f]{64}$/);
    h.requests[0].resolve({pins: [{id: 8, latitude: -1.25, longitude: 2.5, comment: ""}]});
    await load;
    const row = h.elements.get("#community-own-list").children[0];
    assert.equal(row.children[0].textContent, "-1.25°, 2.5° ");
    assert.equal(row.children[1].textContent, "Delete my pin");
    const deleting = row.children[1].fire("click");
    assert.equal(h.requests[1].path, "/api/community/pins/8");
    assert.equal(h.requests[1].options.method, "DELETE");
    h.requests[1].resolve({});
    await flush();
    assert.equal(h.requests[2].path, "/api/community/my-pins");
    h.requests[2].resolve({pins: []});
    await deleting;
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

test("reported 320px left-clipped comment popup is translated back inside its map", async () => {
    const p = panel();
    p.bounds.left = 12;
    p.bounds.width = 296; // map right edge is x=308, matching COMMUNITY-009.
    const h = harness({panels: [p]});
    h.pins();
    const read = h.elements.get("#community-retry").fire("click");
    h.requests[0].resolve({pins: [{id: 1, nickname: "N", comment: "starts clipped", latitude: 1, longitude: 2}]});
    await read;
    const click = h.markers[0].element.fire("click");
    const popup = h.popups[0];
    popup.baseRect = {left: -18, top: 40, width: 180, height: 90};
    assert.equal(popup.element.getBoundingClientRect().left, -18, "the old placement reproduces the reported clipped left edge");
    h.flushFrames();
    await click;
    assert.equal(popup.element.style.translate, "38px 0px");
    assert.equal(popup.element.getBoundingClientRect().left, 20);
    assert.equal(popup.content.children[1].textContent, "starts clipped");
});

test("popup fit handles all four map edges at 320/390/desktop, uses bounded width/height and does not drift on resize", async () => {
    for (const [size, left, width, height] of [["320px", 12, 296, 240], ["390px", 12, 366, 300], ["desktop", 40, 1120, 600]]) {
      for (const [edge, overflow, expected] of [
        ["left", -18, "26px 0px"], ["right", 30, "-38px 0px"],
        ["top", -22, "0px 30px"], ["bottom", 48, "0px -56px"],
      ]) {
        const p = panel();
        p.bounds.left = left;
        p.bounds.width = width;
        p.bounds.height = height;
        const h = harness({panels: [p]});
        h.pins();
        const read = h.elements.get("#community-retry").fire("click");
        const longComment = "x".repeat(500);
        h.requests[0].resolve({pins: [{id: 1, nickname: "N".repeat(40), comment: longComment, latitude: 1, longitude: 2}]});
        await read;
        const click = h.markers[0].element.fire("click");
        const popup = h.popups[0];
        const translation = size === "desktop" && (edge === "top" || edge === "bottom")
            ? `8px ${expected.split(" ")[1]}` : expected;
        popup.baseRect = edge === "left" ? {left: left + overflow, top: 40, width: 180, height: 90}
            : edge === "right" ? {left: left + width - 70, top: 40, width: 100, height: 90}
                : edge === "top" ? {left: 40, top: overflow, width: 100, height: 90}
                    : {left: 40, top: height - 90 + overflow, width: 100, height: 90};
        h.flushFrames();
        await click;
        assert.equal(popup.element.style.translate, translation, `${size} ${edge}`);
        assert.equal(popup.element.classList.values.has("community-map-popup-shifted"), true, `${size} ${edge}`);
        assert.equal(popup.element.style.maxWidth, "240px", `${size} ${edge}`);
        assert.equal(popup.element.style.values.get("--community-popup-height"), `${height - 16}px`, `${size} ${edge}`);
        assert.equal(popup.content.children[0].textContent, "N".repeat(40), `${size} ${edge} long nickname stays text-only`);
        assert.equal(popup.content.children[1].textContent, longComment, `${size} ${edge} long comment stays text-only`);
        assert.equal(popup.content.tabIndex, 0, `${size} ${edge} comment region is keyboard focusable`);
        assert.equal(popup.content.role, "region", `${size} ${edge} comment has region semantics`);
        assert.equal(popup.content["aria-label"], "Community pin comment", `${size} ${edge} comment has an accessible label`);
        popup.baseRect.width = 400;
        popup.baseRect.height = 800;
        p.bounds.width += 30;
        p.bounds.height += 40;
        h.observers.at(-1).trigger();
        h.flushFrames();
        const resized = popup.element.getBoundingClientRect();
        const mapRight = p.bounds.left + p.bounds.width;
        const mapBottom = p.bounds.top + p.bounds.height;
        assert.ok(resized.left >= p.bounds.left + 8, `${size} ${edge} resize keeps popup inside the left inset`);
        assert.ok(resized.right <= mapRight - 8, `${size} ${edge} resize keeps popup inside the right inset`);
        assert.ok(resized.top >= p.bounds.top + 8, `${size} ${edge} resize keeps popup inside the top inset`);
        assert.ok(resized.bottom <= mapBottom - 8, `${size} ${edge} resize keeps popup inside the bottom inset`);
        assert.ok(resized.width <= Math.min(240, p.bounds.width - 16), `${size} ${edge} resized width stays within map policy`);
        assert.ok(resized.height <= p.bounds.height - 16, `${size} ${edge} resized total height stays within map policy`);
        const resizedTranslation = popup.element.style.translate;
        h.observers.at(-1).trigger();
        h.flushFrames();
        assert.equal(popup.element.style.translate, resizedTranslation, `${size} ${edge} repeat resize does not alter the correction`);
        assert.deepEqual(popup.element.getBoundingClientRect(), resized, `${size} ${edge} repeat resize does not drift`);
      }
    }

    const p = panel();
    p.bounds.width = 180;
    p.bounds.height = 120;
    const h = harness({panels: [p]});
    h.pins();
    const read = h.elements.get("#community-retry").fire("click");
    h.requests[0].resolve({pins: [{id: 1, nickname: "Reader", comment: "plain text", latitude: 1, longitude: 2}]});
    await read;
    const click = h.markers[0].element.fire("click");
    const popup = h.popups[0];
    popup.baseRect = {left: 30, top: 20, width: 300, height: 400};
    h.flushFrames();
    await click;
    assert.equal(popup.element.style.maxWidth, "164px", "popup width reserves an 8px inset on each side");
    assert.equal(popup.element.style.values.get("--community-popup-height"), "104px", "popup total height follows map height");
    const css = await readFile(new URL("../static/styles.css", import.meta.url), "utf8");
    // Structural declaration checks only; the fake DOM does not prove browser CSS layout.
    assert.match(css, /\.community-map-popup \.maplibregl-popup-content\s*\{[^}]*overflow:\s*hidden/s);
    assert.match(css, /\.community-popup\s*\{[^}]*overflow-y:\s*auto/s);
    assert.match(css, /\.community-popup\s*\{[^}]*overflow-wrap:\s*anywhere/s);
    assert.equal(popup.content.children[1].textContent, "plain text", "comments remain text-only content");

    for (const width of [16, Number.NaN]) {
        const p = panel();
        p.bounds.width = width;
        const h = harness({panels: [p]});
        h.pins();
        const pending = h.elements.get("#community-retry").fire("click");
        h.requests[0].resolve({pins: [{id: 1, nickname: "Reader", comment: "safe", latitude: 1, longitude: 2}]});
        await pending;
        const open = h.markers[0].element.fire("click");
        h.flushFrames();
        await open;
        assert.equal(h.popups[0].element.style.maxWidth, "", `unsupported map width ${width} skips fitting`);
        assert.equal(h.popups[0].element.style.translate, "none", `unsupported map width ${width} leaves placement untouched`);
    }
});

test("popup fitting disconnects and cancels queued work on close, replacement, refresh, move and map removal", async () => {
    for (const action of ["close", "replacement", "refresh", "move", "remove"]) {
        const p = panel(), h = harness({panels: [p]});
        h.pins();
        const read = h.elements.get("#community-retry").fire("click");
        h.requests[0].resolve({pins: [
            {id: 1, nickname: "First", comment: "first", latitude: 1, longitude: 2},
            {id: 2, nickname: "Second", comment: "second", latitude: 3, longitude: 4},
        ]});
        await read;
        const firstClick = h.markers[0].element.fire("click");
        const popup = h.popups[0];
        assert.equal(h.animationFrames.size, 1, `${action} starts with pending fit frame`);
        const observer = h.observers[0];
        if (action === "close") popup.remove();
        if (action === "replacement") await h.markers[1].element.fire("click");
        if (action === "refresh") h.elements.get("#community-retry").fire("click");
        if (action === "move") p.map.listeners.move();
        if (action === "remove") p.map.listeners.remove();
        await firstClick;
        assert.equal(observer.disconnected, true, `${action} disconnects ResizeObserver`);
        assert.equal(h.animationFrames.size, action === "replacement" ? 1 : 0,
            action === "replacement" ? "only the replacement popup owns a queued fit" : `${action} cancels the pending fit frame`);
        const translationAfterCleanup = popup.element.style.translate;
        h.flushFrames();
        observer.trigger();
        h.flushFrames();
        assert.equal(popup.element.style.translate, translationAfterCleanup, `${action} cannot revive fitting`);
        if (action === "replacement") {
            assert.equal(h.popups.length, 2);
            assert.equal(h.popups[1].content.children[0].textContent, "Second");
        }
    }
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

test("draft preview works without a profile, storage, or network and click matches typed coordinates", async () => {
    const p = panel(), h = harness({panels: [p], denied: true});
    const pins = h.pins();
    const placement = h.elements.get("#community-placement");
    const lat = h.elements.get("#community-latitude");
    const lng = h.elements.get("#community-longitude");
    placement.checked = true;
    await placement.fire("change");
    lat.value = "12.5";
    lng.value = "-34.25";
    await lat.fire("input");
    await lng.fire("input");
    assert.equal(drafts(h).length, 1);
    const marker = drafts(h)[0];
    assert.deepEqual(marker.coordinates, [-34.25, 12.5]);
    assert.equal(marker.map, p.map);
    assert.equal(marker.element.tag, "div");
    assert.equal(marker.element.listeners.click, undefined);
    assert.equal(marker.element.textContent, "Draft pin");
    assert.equal(marker.element["aria-label"], "Unpublished pin preview");
    assert.equal(pins.handleMapClick({lngLat: {lat: 12.5, lng: -34.25}}), true);
    assert.deepEqual(marker.coordinates, [-34.25, 12.5]);
    assert.equal(drafts(h).length, 1);
    assert.deepEqual(h.operations, []);
    assert.equal(h.requests.length, 0);
    assert.equal(h.randomCalls(), 0);
});

test("Add pin here opens and focuses the draft form without storage or requests until consented submit", async () => {
    const h = harness({panels: [panel()]});
    const pins = h.pins();
    assert.equal(pins.addPinHere({lat: 12.25, lng: -34.75}), true);
    assert.equal(h.elements.get("#community-controls").open, true);
    assert.equal(h.elements.get("#community-placement").checked, true);
    assert.equal(h.elements.get("#community-latitude").value, "12.25");
    assert.equal(h.elements.get("#community-longitude").value, "-34.75");
    assert.equal(h.elements.get("#community-comment").focused, true);
    assert.deepEqual(drafts(h)[0].coordinates, [-34.75, 12.25]);
    assert.deepEqual(h.operations, []);
    assert.equal(h.requests.length, 0);

    await activate(h);
    const form = h.elements.get("#community-pin-form");
    await form.fire("submit");
    assert.equal(h.requests.length, 0);
    assert.equal(h.elements.get("#community-public-consent").focused, true);
    h.elements.get("#community-public-consent").checked = true;
    const pending = form.fire("submit");
    assert.equal(h.requests.length, 1);
    assert.deepEqual(JSON.parse(h.requests[0].options.body), {
        nickname: "Reader", comment: "", latitude: 12.25, longitude: -34.75,
    }, "the popup path publishes the same coordinate shape with an optional empty message");
    h.requests[0].resolve({pin: {id: 1}});
    await flush();
    h.requests[1].resolve({pins: [], more: false, next_cursor: null});
    await pending;
});

test("message limit counts trimmed Unicode code points and clears stale custom validity", async () => {
    const templateComment = pinsTemplate.match(/<textarea\b[^>]*id="community-comment"[^>]*>/)?.[0];
    assert.ok(templateComment, "optional message textarea exists");
    assert.doesNotMatch(templateComment, /maxlength/i,
        "native maxlength counts UTF-16 code units and would reject valid Unicode at the boundary");

    for (const message of ["🙂".repeat(500), `  ${"é".repeat(250)}${"🌦️".repeat(125)}  `]) {
        assert.equal(Array.from(message.trim()).length, 500);
        const h = harness();
        h.pins();
        await activate(h);
        h.elements.get("#community-placement").checked = true;
        h.elements.get("#community-latitude").value = "1";
        h.elements.get("#community-longitude").value = "2";
        const comment = h.elements.get("#community-comment");
        comment.value = message;
        await comment.fire("input");
        assert.equal(comment.customValidityMessage, "");
        h.elements.get("#community-public-consent").checked = true;
        const pending = h.elements.get("#community-pin-form").fire("submit");
        assert.equal(h.requests.length, 1, "500 trimmed code points are publishable");
        assert.equal(JSON.parse(h.requests[0].options.body).comment, message,
            "the server receives the entered text and applies its own trimming before storage");
        h.requests[0].resolve({pin: {id: 1}});
        await pending;
    }

    const h = harness();
    h.pins();
    await activate(h);
    h.elements.get("#community-placement").checked = true;
    h.elements.get("#community-latitude").value = "1";
    h.elements.get("#community-longitude").value = "2";
    const comment = h.elements.get("#community-comment");
    comment.value = `  ${"🙂".repeat(501)}  `;
    await comment.fire("input");
    assert.match(comment.customValidityMessage, /500 characters or fewer/);
    comment.reportValidityOverride = true;
    h.elements.get("#community-public-consent").checked = true;
    await h.elements.get("#community-pin-form").fire("submit");
    assert.equal(h.requests.length, 0, "explicit length validation blocks POST even when reportValidity is stubbed true");

    comment.value = ` ${"🙂".repeat(500)} `;
    await comment.fire("input");
    assert.equal(comment.customValidityMessage, "", "valid edits clear the custom validity error");
    assert.equal(comment.validity.customError, false);
    assert.equal(h.elements.get("#community-pin-status").textContent, "");
    h.elements.get("#community-public-consent").checked = true;
    const pending = h.elements.get("#community-pin-form").fire("submit");
    assert.equal(h.requests.length, 1);
    assert.equal(JSON.parse(h.requests[0].options.body).comment, comment.value,
        "valid edits clear the length error and submit the entered text for server-side trimming");
    h.requests[0].resolve({pin: {id: 2}});
    await pending;
});

test("blank, whitespace, non-finite and out-of-range edits clear drafts instead of showing zero", async () => {
    const h = harness({panels: [panel()]});
    h.pins();
    const placement = h.elements.get("#community-placement");
    const lat = h.elements.get("#community-latitude");
    const lng = h.elements.get("#community-longitude");
    placement.checked = true;
    lat.value = "0";
    lng.value = "0";
    await placement.fire("change");
    assert.deepEqual(drafts(h).at(-1).coordinates, [0, 0]);
    for (const [latitude, longitude] of [["", "0"], ["   ", "0"], ["0", ""], ["0", "  "],
        ["NaN", "0"], ["Infinity", "0"], ["0", "-Infinity"], ["85.01", "0"],
        ["-85.01", "0"], ["0", "180.01"], ["0", "-180.01"]]) {
        lat.value = latitude;
        lng.value = longitude;
        await lat.fire("input");
        await lng.fire("input");
        assert.equal(drafts(h).filter(marker => !marker.removed).length, 0, `${latitude}, ${longitude}`);
    }
    lat.value = "-85";
    lng.value = "180";
    await lng.fire("input");
    assert.deepEqual(drafts(h).at(-1).coordinates, [180, -85]);
    assert.equal(h.requests.length, 0);
});

test("invalid coordinates cannot publish even with a profile and public consent", async () => {
    const h = harness({panels: [panel()]});
    h.pins();
    await activate(h);
    h.elements.get("#community-placement").checked = true;
    h.elements.get("#community-comment").value = "Comment";
    h.elements.get("#community-public-consent").checked = true;
    const lat = h.elements.get("#community-latitude");
    const lng = h.elements.get("#community-longitude");
    const form = h.elements.get("#community-pin-form");
    for (const [latitude, longitude] of [["", "0"], ["  ", "0"], ["NaN", "0"],
        ["Infinity", "0"], ["86", "0"], ["0", "181"]]) {
        lat.value = latitude;
        lng.value = longitude;
        await form.fire("submit");
        assert.equal(h.requests.length, 0, `${latitude}, ${longitude}`);
        assert.match(h.elements.get("#community-pin-status").textContent, /valid pin coordinates/);
    }
});

test("edits reuse one draft per map; late load adds a draft and removal releases only that map", async () => {
    const first = panel(), late = panel(false), h = harness({panels: [first, late]});
    h.pins();
    const placement = h.elements.get("#community-placement");
    const lat = h.elements.get("#community-latitude");
    const lng = h.elements.get("#community-longitude");
    placement.checked = true;
    lat.value = "10";
    lng.value = "20";
    await placement.fire("change");
    assert.equal(drafts(h).length, 1);
    for (let value = 21; value < 25; value++) {
        lng.value = String(value);
        await lng.fire("input");
    }
    assert.equal(drafts(h).length, 1);
    assert.deepEqual(drafts(h)[0].coordinates, [24, 10]);
    late.map.listeners.load();
    late.styleReady = true; // The map owner marks readiness after its load listeners run.
    await flush();
    assert.equal(drafts(h).length, 2);
    assert.deepEqual(drafts(h).map(marker => marker.coordinates), [[24, 10], [24, 10]]);
    lat.value = "11";
    await lat.fire("input");
    assert.equal(drafts(h).length, 2);
    assert.deepEqual(drafts(h).map(marker => marker.coordinates), [[24, 11], [24, 11]]);
    late.map.listeners.remove();
    assert.equal(drafts(h)[1].removed, true);
    assert.equal(drafts(h)[0].removed, undefined);
    lng.value = "25";
    await lng.fire("input");
    assert.equal(drafts(h).length, 2);
    assert.deepEqual(drafts(h)[0].coordinates, [25, 11]);
    assert.equal(h.requests.length, 0);
});

test("public refresh and pan preserve the distinct non-interactive draft", async () => {
    const p = panel(), h = harness({panels: [p]});
    h.pins();
    h.elements.get("#community-placement").checked = true;
    h.elements.get("#community-latitude").value = "1";
    h.elements.get("#community-longitude").value = "2";
    await h.elements.get("#community-placement").fire("change");
    const draft = drafts(h)[0];
    const pending = h.elements.get("#community-retry").fire("click");
    h.requests[0].resolve({pins: [{id: 1, nickname: "Reader", comment: "Public", latitude: 3, longitude: 4}], more: false, next_cursor: null});
    await pending;
    assert.equal(h.markers.filter(marker => marker.element.className === "community-marker").length, 1);
    assert.equal(draft.removed, undefined);
    p.map.listeners.move();
    p.map.listeners.moveend();
    assert.equal(draft.removed, undefined);
    assert.deepEqual(draft.coordinates, [2, 1]);
    assert.equal(h.markers[1].removed, true);
});

test("placement off and successful publish clear drafts; failed publish preserves them and consent", async () => {
    const h = harness({panels: [panel()]});
    h.pins();
    const placement = h.elements.get("#community-placement");
    const lat = h.elements.get("#community-latitude");
    const lng = h.elements.get("#community-longitude");
    placement.checked = true;
    lat.value = "1";
    lng.value = "2";
    await placement.fire("change");
    placement.checked = false;
    await placement.fire("change");
    assert.equal(drafts(h)[0].removed, true);
    await activate(h);
    placement.checked = true;
    await placement.fire("change");
    const draft = drafts(h).at(-1);
    const consent = h.elements.get("#community-public-consent");
    consent.checked = true;
    h.elements.get("#community-comment").value = "Comment";
    const form = h.elements.get("#community-pin-form");
    const failed = form.fire("submit");
    h.requests.at(-1).resolve({error: "Please retry"}, false);
    await failed;
    assert.equal(draft.removed, undefined);
    assert.equal(placement.checked, true);
    assert.equal(consent.checked, true);
    assert.match(h.elements.get("#community-pin-status").textContent, /Please retry/);
    const succeeded = form.fire("submit");
    h.requests.at(-1).resolve({pin: {id: 1}});
    await flush();
    assert.equal(draft.removed, true);
    assert.equal(placement.checked, false);
    assert.equal(consent.checked, false);
    h.requests.at(-1).resolve({pins: [], more: false, next_cursor: null});
    await succeeded;
});

test("disabled community remains inert for typed edits, map clicks, refresh and submit", async () => {
    const h = harness({enabled: false, panels: [panel()]});
    const pins = h.pins();
    h.elements.get("#community-placement").checked = true;
    h.elements.get("#community-latitude").value = "1";
    h.elements.get("#community-longitude").value = "2";
    await h.elements.get("#community-placement").fire("change");
    await h.elements.get("#community-latitude").fire("input");
    assert.equal(pins.handleMapClick({lngLat: {lat: 3, lng: 4}}), false);
    assert.equal(pins.addPinHere, null);
    await h.elements.get("#community-retry").fire("click");
    await h.elements.get("#community-pin-form").fire("submit");
    assert.equal(drafts(h).length, 0);
    assert.deepEqual(h.operations, []);
    assert.equal(h.requests.length, 0);
});
