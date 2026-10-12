// Local storage is touched only after an explicit profile action.
const STORAGE_KEY = "climate.community.profile.v1";
const PROFILE_DAYS = 30;
const PROFILE_MS = PROFILE_DAYS * 24 * 60 * 60 * 1000;

export function createLocalProfile({root = document, onChange = () => {}} = {}) {
    const open = root.querySelector("#community-profile-open");
    const form = root.querySelector("#community-profile-form");
    const nickname = root.querySelector("#community-nickname");
    const consent = root.querySelector("#community-storage-consent");
    const status = root.querySelector("#community-profile-status");
    const forget = root.querySelector("#community-profile-forget");
    let profile = null;
    let expiryTimer;
    function scheduleExpiry() {
        clearTimeout(expiryTimer);
        if (!profile) return;
        const delay = Math.min(Math.max(0, profile.expiresAt - Date.now()), 2_147_000_000);
        expiryTimer = setTimeout(() => {
            if (!expire()) scheduleExpiry();
        }, delay);
    }
    function activate(value, message = "") {
        clearTimeout(expiryTimer);
        profile = value;
        forget.hidden = !profile;
        form.hidden = !!profile;
        status.textContent = message || (profile
            ? `Local profile active: ${profile.nickname}. Device ownership expires ${new Date(profile.expiresAt).toLocaleDateString()}.`
            : "No active local profile.");
        onChange(profile);
        scheduleExpiry();
    }
    function valid(value) {
        return value?.consent === true && typeof value.nickname === "string"
            && value.nickname.trim().length >= 1 && value.nickname.length <= 40
            && typeof value.token === "string" && /^[0-9a-f]{64}$/.test(value.token)
            && (!Object.hasOwn(value, "expiresAt")
                || (typeof value.expiresAt === "number" && Number.isFinite(value.expiresAt)
                    && value.expiresAt > 0));
    }
    function expire() {
        if (!profile || Date.now() < profile.expiresAt) return false;
        consent.checked = false;
        activate(null, "This local profile expired after 30 days. Its public pins remain, but this device can no longer delete them. Reuse this device to remove the expired record, then create a new profile if needed.");
        return true;
    }
    function get() {
        expire();
        return profile;
    }
    open.addEventListener("click", () => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            const value = saved ? JSON.parse(saved) : null;
            if (valid(value)) {
                if (Number.isFinite(value.expiresAt) && value.expiresAt <= Date.now()) {
                    consent.checked = false;
                    localStorage.removeItem(STORAGE_KEY);
                    activate(null, "This local profile expired after 30 days. Its public pins remain and this device has lost their deletion credential. Create a new profile with fresh consent to publish again.");
                } else {
                    // A legacy, explicitly reused profile keeps its ownership token
                    // and starts its one fixed remembrance period now.
                    const upgraded = Number.isFinite(value.expiresAt)
                        ? value : {...value, expiresAt: Date.now() + PROFILE_MS};
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(upgraded));
                    activate(upgraded);
                }
            }
            else {
                activate(null);
                form.hidden = false;
                status.textContent = "Choose a nickname and agree to local storage to create a profile. Profiles are remembered for 30 days; after expiry, public pins remain but this device loses deletion access.";
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
                token: Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join(""),
                expiresAt: Date.now() + PROFILE_MS};
            localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
            activate(value);
        } catch {
            activate(null);
            status.textContent = "Could not save this profile. No pin will be published and no alternative identity was created.";
        }
    });
    forget.addEventListener("click", () => {
        if (!confirm("Forget this device's local profile? Already public pins will remain. This device will lose the credential needed to delete those pins yourself.")) return;
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
    return {get};
}
