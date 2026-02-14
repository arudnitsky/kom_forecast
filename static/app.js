/**
 * KOM-Forecast client-side logic.
 *
 * Responsibilities:
 *   1. Theme toggling (light/dark) with localStorage persistence.
 *   2. Settings form: load from localStorage, save to localStorage, reload page with new params.
 *   3. Reset settings to server-side defaults via /api/config.
 *   4. On page load, auto-apply stored settings as query parameters if they differ from current.
 */

const STORAGE_KEY_THEME = "kom-theme";
const STORAGE_KEY_SETTINGS = "kom-settings";

/* ================================================================
   Theme Toggle
   ================================================================ */

/**
 * Apply theme to <html> element and update the toggle icon.
 * @param {string} theme - "light" or "dark"
 */
function applyTheme(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
    const icon = document.getElementById("theme-icon");
    if (icon) {
        icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
    }
}

/**
 * Initialize theme from localStorage or system preference.
 */
function initTheme() {
    const stored = localStorage.getItem(STORAGE_KEY_THEME);
    if (stored) {
        applyTheme(stored);
    } else {
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        applyTheme(prefersDark ? "dark" : "light");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();

    const toggleBtn = document.getElementById("theme-toggle");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("data-bs-theme");
            const next = current === "dark" ? "light" : "dark";
            localStorage.setItem(STORAGE_KEY_THEME, next);
            applyTheme(next);
        });
    }

    initSettings();
});

/* ================================================================
   Settings Persistence
   ================================================================ */

/**
 * Return the currently stored settings object, or null if none exist.
 * @returns {object|null} Settings with keys: min_wind_speed, direction_tolerance, quality_percentage
 */
function loadSettings() {
    const raw = localStorage.getItem(STORAGE_KEY_SETTINGS);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

/**
 * Save settings object to localStorage.
 * @param {object} settings
 */
function saveSettings(settings) {
    localStorage.setItem(STORAGE_KEY_SETTINGS, JSON.stringify(settings));
}

/**
 * Read current settings from the form inputs.
 * @returns {object}
 */
function readFormSettings() {
    return {
        min_wind_speed: parseFloat(document.getElementById("min_wind_speed").value),
        direction_tolerance: parseFloat(document.getElementById("direction_tolerance").value),
        quality_percentage: parseInt(document.getElementById("quality_percentage").value, 10),
    };
}

/**
 * Reload the page with settings as query parameters so the server uses them.
 * @param {object} settings
 */
function reloadWithSettings(settings) {
    const params = new URLSearchParams();
    params.set("min_wind_speed", settings.min_wind_speed);
    params.set("direction_tolerance", settings.direction_tolerance);
    params.set("quality_percentage", settings.quality_percentage);
    window.location.search = params.toString();
}

/**
 * Populate form fields from a settings object.
 * @param {object} settings
 */
function populateForm(settings) {
    if (settings.min_wind_speed !== undefined) {
        document.getElementById("min_wind_speed").value = settings.min_wind_speed;
    }
    if (settings.direction_tolerance !== undefined) {
        document.getElementById("direction_tolerance").value = settings.direction_tolerance;
    }
    if (settings.quality_percentage !== undefined) {
        document.getElementById("quality_percentage").value = settings.quality_percentage;
    }
}

/**
 * Initialize settings: populate form from localStorage, handle save/reset buttons,
 * and auto-reload with stored settings if the URL doesn't already have them.
 */
function initSettings() {
    const stored = loadSettings();

    // If settings exist in localStorage, populate the form
    if (stored) {
        populateForm(stored);
    }

    // If settings are stored but not reflected in URL, reload with them
    const urlParams = new URLSearchParams(window.location.search);
    if (stored && !urlParams.has("min_wind_speed")) {
        reloadWithSettings(stored);
        return; // page will reload
    }

    // Save & Reload button
    const saveBtn = document.getElementById("save-settings");
    if (saveBtn) {
        saveBtn.addEventListener("click", () => {
            const settings = readFormSettings();
            saveSettings(settings);
            reloadWithSettings(settings);
        });
    }

    // Reset to Defaults button
    const resetBtn = document.getElementById("reset-settings");
    if (resetBtn) {
        resetBtn.addEventListener("click", async () => {
            try {
                const resp = await fetch("/api/config");
                const defaults = await resp.json();
                localStorage.removeItem(STORAGE_KEY_SETTINGS);
                populateForm(defaults);
                // Reload without query params to use server defaults
                window.location.href = "/";
            } catch (err) {
                console.error("Failed to fetch defaults:", err);
            }
        });
    }
}
