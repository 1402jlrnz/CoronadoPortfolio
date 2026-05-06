(() => {
    const DEFAULT_PROJECT_ID = "vRreNjMMAsR6hOJbUoVv";

    function getProjectId() {
        const pageProjectId = document.body?.dataset?.unicornProject;
        return pageProjectId || DEFAULT_PROJECT_ID;
    }

    function ensureBackgroundContainer() {
        if (document.querySelector("[data-us-project]")) {
            return;
        }

        const container = document.createElement("div");
        container.className = "unicorn-background";
        container.setAttribute("data-us-project", getProjectId());
        container.setAttribute("aria-hidden", "true");
        document.body.prepend(container);
    }

    function initUnicorn() {
        const unicorn = window.UnicornStudio;
        if (!unicorn || typeof unicorn.init !== "function") {
            return;
        }

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", () => unicorn.init(), { once: true });
            return;
        }

        unicorn.init();
    }

    function loadUnicornScript() {
        if (window.UnicornStudio && typeof window.UnicornStudio.init === "function") {
            initUnicorn();
            return;
        }

        if (!window.UnicornStudio) {
            window.UnicornStudio = { isInitialized: false };
        }

        const existingScript = document.querySelector('script[src*="unicornstudio.js"]');
        if (existingScript) {
            existingScript.addEventListener("load", initUnicorn, { once: true });
            return;
        }

        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/gh/hiunicornstudio/unicornstudio.js@v2.1.12/dist/unicornStudio.umd.js";
        script.onload = initUnicorn;
        (document.head || document.body).appendChild(script);
    }

    ensureBackgroundContainer();
    loadUnicornScript();
})();
