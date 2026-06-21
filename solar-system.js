const scriptCache = new Map();

function buildPlanetCard(planet, index) {
    const article = document.createElement("article");
    article.className = "planet-card glass panel panel-accent";
    article.innerHTML = `
        <div class="planet-card-top">
            <span class="planet-index">${String(index + 1).padStart(2, "0")}</span>
            <div class="planet-copy">
                <h3>${planet.name}</h3>
                <p>${planet.description}</p>
                <div class="chip-row">
                    ${planet.chips.map((chip) => `<span class="chip">${chip}</span>`).join("")}
                </div>
            </div>
        </div>
        <div class="media-frame media-frame--interactive">
            <video controls preload="metadata" playsinline>
                <source src="${planet.video}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        <div class="asset-bar">
            <a class="btn btn-ghost asset-btn" href="python/${planet.id}.py" download>
                Download Python
            </a>
            <a class="btn btn-ghost asset-btn" href="blender_files/${planet.id}.blend" download>
                Download Blender
            </a>
            <button class="btn btn-ghost view-script-btn" type="button" data-planet="${planet.id}">
                View Script
            </button>
            <button class="btn btn-primary copy-script-btn" type="button" data-planet="${planet.id}">
                Copy Script
            </button>
        </div>
        <div class="script-panel" id="script-panel-${planet.id}" hidden>
            <div class="script-panel-head">
                <span>Blender Python Script</span>
                <button class="btn btn-ghost script-toggle" type="button" data-planet="${planet.id}">
                    Hide
                </button>
            </div>
            <pre class="script-code"><code id="script-code-${planet.id}">Loading script...</code></pre>
        </div>
    `;
    return article;
}

async function loadScript(planetId) {
    if (scriptCache.has(planetId)) {
        return scriptCache.get(planetId);
    }

    const response = await fetch(`python/${planetId}.py`);
    if (!response.ok) {
        throw new Error(`Could not load python/${planetId}.py`);
    }

    const text = await response.text();
    scriptCache.set(planetId, text);
    return text;
}

async function showScript(planetId) {
    const panel = document.getElementById(`script-panel-${planetId}`);
    const code = document.getElementById(`script-code-${planetId}`);
    const viewButton = document.querySelector(`.view-script-btn[data-planet="${planetId}"]`);

    if (!panel || !code) {
        return;
    }

    panel.hidden = false;
    if (viewButton) {
        viewButton.hidden = true;
    }

    try {
        code.textContent = await loadScript(planetId);
    } catch (error) {
        code.textContent = "Script unavailable.";
    }
}

async function copyScript(planetId) {
    const button = document.querySelector(`.copy-script-btn[data-planet="${planetId}"]`);
    try {
        const script = await loadScript(planetId);
        await navigator.clipboard.writeText(script);
        if (button) {
            const original = button.textContent;
            button.textContent = "Copied!";
            setTimeout(() => {
                button.textContent = original;
            }, 1600);
        }
    } catch (error) {
        if (button) {
            button.textContent = "Copy failed";
            setTimeout(() => {
                button.textContent = "Copy Script";
            }, 1600);
        }
    }
}

function renderPlanetCatalog() {
    const mount = document.getElementById("planet-catalog");
    if (!mount || !Array.isArray(PLANET_CATALOG)) {
        return;
    }

    mount.replaceChildren();
    PLANET_CATALOG.forEach((planet, index) => {
        mount.appendChild(buildPlanetCard(planet, index));
    });
}

document.addEventListener("click", (event) => {
    const viewButton = event.target.closest(".view-script-btn");
    if (viewButton) {
        showScript(viewButton.dataset.planet);
        return;
    }

    const hideButton = event.target.closest(".script-toggle");
    if (hideButton) {
        const planetId = hideButton.dataset.planet;
        const panel = document.getElementById(`script-panel-${planetId}`);
        const viewBtn = document.querySelector(`.view-script-btn[data-planet="${planetId}"]`);
        if (panel) {
            panel.hidden = true;
        }
        if (viewBtn) {
            viewBtn.hidden = false;
        }
        return;
    }

    const copyButton = event.target.closest(".copy-script-btn");
    if (copyButton) {
        copyScript(copyButton.dataset.planet);
    }
});

document.addEventListener("DOMContentLoaded", renderPlanetCatalog);
