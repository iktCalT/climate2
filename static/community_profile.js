// Local storage is touched only after an explicit profile action.
const STORAGE_KEY = "climate.community.profile.v1";

export function createLocalProfile({root = document, onChange = () => {}} = {}) {
    const open = root.querySelector("#community-profile-open");
    const form = root.querySelector("#community-profile-form");
    const nickname = root.querySelector("#community-nickname");
    const consent = root.querySelector("#community-storage-consent");
    const status = root.querySelector("#community-profile-status");
    const forget = root.querySelector("#community-profile-forget");
    let profile = null;
    function activate(value) {
        profile = value;
        forget.hidden = !profile;
        form.hidden = !!profile;
        status.textContent = profile ? `Local profile active: ${profile.nickname}.` : "No active local profile.";
        onChange(profile);
    }
    function valid(value) {
        return value?.consent === true && typeof value.nickname === "string"
            && value.nickname.trim().length >= 1 && value.nickname.length <= 40
            && typeof value.token === "string" && /^[0-9a-f]{64}$/.test(value.token);
    }
    open.addEventListener("click", () => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            const value = saved ? JSON.parse(saved) : null;
            if (valid(value)) {
                // A saved profile remains usable only while consented storage
                // is available; do not switch to an in-memory-only identity.
                localStorage.setItem(STORAGE_KEY, saved);
                activate(value);
            }
            else {
                activate(null);
                form.hidden = false;
                status.textContent = "Choose a nickname and agree to local storage to create a profile.";
            }
        } catch {
            activate(null);
            status.textContent = "Local storage is unavailable. This device cannot publish pins; no alternative identity was created.";
        }
    });
    form.addEventListener("submit", event => {
        event.preventDefault();
        if (!form.reportValidity() || !consent.checked || !nickname.value.trim()) return;
        try {
            const bytes = new Uint8Array(32);
            crypto.getRandomValues(bytes);
            const value = {nickname: nickname.value.trim(), consent: true,
                token: Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("")};
            localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
            activate(value);
        } catch {
            activate(null);
            status.textContent = "Could not save this profile. No pin will be published and no alternative identity was created.";
        }
    });
    forget.addEventListener("click", () => {
        try {
            localStorage.removeItem(STORAGE_KEY);
            activate(null);
            status.textContent = "Device profile forgotten. Already public pins remain; this device has lost their deletion credential.";
        } catch {
            activate(null);
            forget.hidden = false;
            status.textContent = "Could not clear local storage. The saved profile may remain on this device.";
        }
    });
    return {get: () => profile};
}
