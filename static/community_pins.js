import {createLocalProfile} from "/static/community_profile.js";

async function api(path, options = {}) {
    const response = await fetch(path, {credentials: "same-origin", ...options});
    let data;
    try { data = await response.json(); }
    catch { throw new Error("Community service returned an unreadable response. Please retry."); }
    if (!response.ok) throw new Error(data.error || "Community request failed. Please retry.");
    return data;
}

export function createCommunityPins({panels = [], Marker, Popup, root = document} = {}) {
    const controls = root.querySelector("#community-controls");
    const enabled = controls?.dataset.enabled === "true";
    const adminCsrf = controls?.dataset.adminCsrf;
    const form = root.querySelector("#community-pin-form");
    const placement = root.querySelector("#community-placement");
    const latitude = root.querySelector("#community-latitude");
    const longitude = root.querySelector("#community-longitude");
    const publish = root.querySelector("#community-publish");
    const pinStatus = root.querySelector("#community-pin-status");
    const readStatus = root.querySelector("#community-read-status");
    const moreButton = root.querySelector("#community-more");
    const profileStatus = root.querySelector("#community-profile-status");
    const ownList = root.querySelector("#community-own-list");
    const ownControls = root.querySelector("#community-own-pins");
    const markerSets = new Map();
    const removed = new Set();
    let pins = [], nextCursor = null, controller, timer, generation = 0, popup;
    let ownGeneration = 0, ownController, publishing = false, loading = false;
    const live = () => panels.filter(panel => !panel.removed && !removed.has(panel) && panel.styleReady);
    const profile = createLocalProfile({root, onChange() {
        ownGeneration++;
        ownController?.abort();
        ownList.replaceChildren();
        ownControls.hidden = !enabled || !profile.get();
        if (publish) publish.disabled = !enabled || !profile.get() || publishing;
    }});

    function writeOptions(token, method = "DELETE", payload = {}, admin = false) {
        return {method, headers: {"Content-Type": "application/json", "X-Community-Token": token,
            ...(admin ? {"X-Community-CSRF": adminCsrf} : {})}, body: JSON.stringify(payload)};
    }
    async function removePin(id, admin = false) {
        const identity = profile.get();
        if (!admin && !identity) throw new Error("Activate your saved local profile to delete your pins.");
        await api(`/api/community/${admin ? "admin/" : ""}pins/${id}`,
            writeOptions(admin ? adminCsrf : identity.token, "DELETE", {}, admin));
        popup?.remove();
        if (pinStatus) pinStatus.textContent = "Public pin deleted.";
        if (panels.length) await refresh();
        if (profile.get()) await loadOwnPins();
    }
    async function loadOwnPins() {
        const identity = profile.get();
        if (!enabled || !identity) return;
        const current = ++ownGeneration;
        ownController?.abort();
        ownController = new AbortController();
        try {
            // This private credential is sent only to the own-pin endpoint.
            const data = await api("/api/community/my-pins", {signal: ownController.signal,
                headers: {"X-Community-Token": identity.token}});
            if (current !== ownGeneration || identity !== profile.get()) return;
            ownList.replaceChildren();
            for (const pin of data.pins) {
                const item = document.createElement("li");
                const text = document.createElement("span");
                text.className = "community-comment";
                text.textContent = `${pin.latitude}°, ${pin.longitude}°: ${pin.comment} `;
                const button = document.createElement("button");
                button.type = "button";
                button.textContent = "Delete my pin";
                button.addEventListener("click", async () => {
                    button.disabled = true;
                    try { await removePin(pin.id); }
                    catch (error) { profileStatus.textContent = error.message; }
                    finally { button.disabled = false; }
                });
                item.append(text, button);
                ownList.append(item);
            }
            profileStatus.textContent = `${data.pins.length} active public pins on this device identity. Delete pins before forgetting the device.`;
        } catch (error) {
            if (current === ownGeneration && error.name !== "AbortError") profileStatus.textContent = error.message;
        }
    }
    root.querySelector("#community-own-refresh").addEventListener("click", loadOwnPins);

    function clearMarkers(panel) {
        for (const marker of markerSets.get(panel) || []) marker.remove();
        markerSets.delete(panel);
    }
    function render() {
        for (const panel of live()) {
            clearMarkers(panel);
            const markers = [];
            for (const pin of pins) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "community-marker";
                button.textContent = "●";
                button.setAttribute("aria-label", `Read community comment by ${pin.nickname}`);
                button.addEventListener("click", event => {
                    event.stopPropagation();
                    popup?.remove();
                    const content = document.createElement("div");
                    content.className = "community-popup";
                    const name = document.createElement("strong");
                    name.textContent = pin.nickname;
                    const comment = document.createElement("p");
                    comment.className = "community-comment";
                    comment.textContent = pin.comment;
                    content.append(name, comment);
                    if (adminCsrf) {
                        const remove = document.createElement("button");
                        remove.type = "button";
                        remove.textContent = "Remove as administrator";
                        remove.addEventListener("click", async () => {
                            remove.disabled = true;
                            try { await removePin(pin.id, true); }
                            catch (error) { pinStatus.textContent = error.message; }
                            finally { remove.disabled = false; }
                        });
                        content.append(remove);
                    }
                    popup = new Popup().setLngLat([pin.longitude, pin.latitude]).setDOMContent(content).addTo(panel.map);
                });
                markers.push(new Marker({element: button}).setLngLat([pin.longitude, pin.latitude]).addTo(panel.map));
            }
            markerSets.set(panel, markers);
        }
    }
    function invalidate() {
        generation++;
        controller?.abort();
        clearTimeout(timer);
        loading = false;
        pins = [];
        nextCursor = null;
        popup?.remove();
        for (const panel of panels) clearMarkers(panel);
        if (moreButton) moreButton.hidden = true;
    }
    async function refresh(append = false) {
        if (!enabled || !panels.length) return;
        const panel = live()[0];
        if (!panel) return;
        if (append && (loading || nextCursor === null)) return;
        if (!append) invalidate();
        const current = generation;
        controller = new AbortController();
        loading = true;
        moreButton.disabled = true;
        const bounds = panel.map.getBounds();
        const viewport = {south: Math.max(-85, bounds.getSouth()), north: Math.min(85, bounds.getNorth()),
            west: Math.max(-180, bounds.getWest()), east: Math.min(180, bounds.getEast())};
        if (viewport.south >= viewport.north || viewport.west >= viewport.east) {
            loading = false;
            readStatus.textContent = "Move the map into the supported world to read community pins.";
            return;
        }
        const query = new URLSearchParams({...viewport, limit: 100, cursor: append ? nextCursor : 0});
        readStatus.textContent = "Loading public community pins…";
        try {
            // Anonymous public reads never carry an ownership token.
            const data = await api(`/api/community/pins?${query}`, {signal: controller.signal});
            if (current !== generation || panel.removed || removed.has(panel)) return;
            pins = append ? [...pins, ...data.pins] : data.pins;
            nextCursor = data.next_cursor;
            render();
            moreButton.hidden = !data.more;
            readStatus.textContent = `${pins.length} public pins loaded for this view. ${data.more ? "More pins are available; use Load more visible pins." : "No further pins on this page sequence."}`;
        } catch (error) {
            if (current === generation && error.name !== "AbortError") readStatus.textContent = `${error.message} Use Refresh visible pins to retry.`;
        } finally {
            if (current === generation) {
                loading = false;
                moreButton.disabled = false;
            }
        }
    }
    function schedule() {
        clearTimeout(timer);
        if (enabled && live().length) timer = setTimeout(() => refresh(), 350);
    }
    root.querySelector("#community-retry")?.addEventListener("click", () => refresh());
    moreButton?.addEventListener("click", () => refresh(true));
    form?.addEventListener("submit", async event => {
        event.preventDefault();
        const identity = profile.get();
        if (!enabled || !identity || publishing) return;
        if (!placement.checked) {
            pinStatus.textContent = "Enable Place a pin before publishing.";
            return;
        }
        if (!form.reportValidity()) return;
        publishing = true;
        publish.disabled = true;
        try {
            await api("/api/community/pins", writeOptions(identity.token, "POST", {
                nickname: identity.nickname, comment: root.querySelector("#community-comment").value,
                latitude: Number(latitude.value), longitude: Number(longitude.value),
            }));
            pinStatus.textContent = "Your pin and comment are now public.";
            placement.checked = false;
            root.querySelector("#community-public-consent").checked = false;
            await refresh();
        } catch (error) { pinStatus.textContent = error.message; }
        finally {
            publishing = false;
            publish.disabled = !enabled || !profile.get();
        }
    });
    for (const panel of panels) {
        panel.map.on("load", () => queueMicrotask(schedule));
        panel.map.on("move", invalidate);
        panel.map.on("moveend", schedule);
        panel.map.on("remove", () => {
            removed.add(panel);
            invalidate();
            schedule();
        });
    }
    return {handleMapClick(event) {
        if (!enabled || !placement?.checked) return false;
        latitude.value = event.lngLat.lat;
        longitude.value = event.lngLat.lng;
        pinStatus.textContent = "Pin coordinates selected. Enter a comment and explicitly publish it when ready.";
        return true;
    }};
}
