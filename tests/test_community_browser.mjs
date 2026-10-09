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
function harness({denied = false, enabled = true, panels = [], confirmResult = true} = {}) {
    const elements = new Map();
    for (const id of [...profileTemplate.matchAll(/id="([^"]+)"/g), ...pinsTemplate.matchAll(/id="([^"]+)"/g)]) elements.set("#" + id[1], element());
    elements.get("#community-controls").dataset.enabled = String(enabled);
    const root = {querySelector: id => elements.get(id) || null};
    const operations = [], requests = [], markers = [], popups = [], timers = new Map(), confirmations = [];
    let saved = null, randomCalls = 0, serial = 0, removeDenied = false;
    const storage = {getItem() { operations.push("read"); if (denied) throw Error(); return saved; },
        setItem(_, value) { operations.push("write"); if (denied) throw Error(); saved = value; },
        removeItem() { operations.push("remove"); if (denied || removeDenied) throw Error(); saved = null; }};
    const crypto = {getRandomValues(bytes) { randomCalls++; assert.equal(bytes.length, 32); bytes.fill(171); return bytes; }};
    const fetch = (path, options) => new Promise(resolve => requests.push({path, options,
        resolve: (data, ok = true) => resolve({ok, json: async () => data})}));
    class Marker { constructor({element}) { this.element = element; markers.push(this); } setLngLat(value) {this.coordinates = value; return this;} addTo(map) {this.map = map; return this;} remove() {this.removed = true;} }
    class Popup { constructor() {popups.push(this);} setLngLat() {return this;} setDOMContent(content) {this.content = content; return this;} addTo() {return this;} remove() {this.removed = true;} }
    const make = new Function("localStorage", "crypto", "document", "fetch", "setTimeout", "clearTimeout", "queueMicrotask", "confirm", profileSource + "\n" + pinsSource + "\nreturn {createLocalProfile, createCommunityPins};");
    const functions = make(storage, crypto, {createElement: element}, fetch,
        callback => {timers.set(++serial, callback); return serial;}, id => timers.delete(id), queueMicrotask,
        message => {confirmations.push(message); return confirmResult;});
    return {root, elements, operations, requests, markers, popups, timers, confirmations, panels, Marker, Popup, functions,
        randomCalls: () => randomCalls, saved: () => saved,
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
    return {styleReady, map: {listeners: {}, on(name, callback) {this.listeners[name] = callback;},
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
    await h.elements.get("#community-retry").fire("click");
    await h.elements.get("#community-pin-form").fire("submit");
    assert.equal(drafts(h).length, 0);
    assert.deepEqual(h.operations, []);
    assert.equal(h.requests.length, 0);
});
