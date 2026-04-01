
document.addEventListener("DOMContentLoaded", async () => {
    await loadRecommendations();
    const refreshBtn = document.getElementById("refresh-recommendations-btn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", async () => {

            refreshBtn.disabled = true;
            refreshBtn.textContent = "Loading...";
            refreshBtn.style.opacity = "0.6";
            refreshBtn.style.cursor = "not-allowed";

            await loadRecommendations();

            refreshBtn.disabled = false;
            refreshBtn.textContent = "Refresh ↻";
            refreshBtn.style.opacity = "1";
            refreshBtn.style.cursor = "pointer";
        });
    }
});

async function loadRecommendations() {
    const container = document.getElementById("recommendations");
    container.innerHTML = "<p>Loading AI recommendations...</p>";
    try {
        const res = await fetch("/api/recommend");
        const data = await res.json();

        if (!res.ok) {
            container.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
            return;
        }
        renderRecommendations(data.results, container);
    } catch (err) {
        container.innerHTML = `<p style="color: red;">Error loading recommendations.</p>`;
    }
}

function renderRecommendations(results, container) {
    container.innerHTML = "";
    if (!results || results.length === 0) {
        container.innerHTML = "<p>No recommendations found.</p>";
        return;
    }

    results.forEach((show) => {
        const card = document.createElement("div");
        card.className = "result-card";
        const currentStatus = show.user_status;

        card.innerHTML = `
            <h3>${show.name}</h3>
            ${show.image ? `<img src="${show.image.medium}" alt="${show.name}">` : ""}
            <div id="action-buttons-${show.id}" class="action-buttons" style="display: flex; gap: 8px; padding: 16px; border-top: 1px solid var(--border);">
                </div>
        `;
        container.appendChild(card);

        renderButtons(card, show, currentStatus);
    });
}

function renderButtons(card, show, status) {
    const actionDiv = card.querySelector(`#action-buttons-${show.id}`);
    actionDiv.innerHTML = ""; 

    if (["0", "1", "2"].includes(status)) {
        // Like, Neutral, Dislike
        const btnLike = createButton("Like", status === "0", "0", () => rateRecommended(show, "0", card));
        const btnNeutral = createButton("Neutral", status === "1", "1", () => rateRecommended(show, "1", card));
        const btnDislike = createButton("Dislike", status === "2", "2", () => rateRecommended(show, "2", card));
        actionDiv.append(btnLike, btnNeutral, btnDislike);
    } else {
        // Watched, Interested, Not Interested
        const btnWatched = createButton("Watched", false, null, () => renderButtons(card, show, "0"));
        const btnInterested = createButton("Interested", status === "3", "3", () => rateRecommended(show, "3", card));
        const btnNotInt = createButton("Not Int.", status === "4", "4", () => rateRecommended(show, "4", card));
        actionDiv.append(btnWatched, btnInterested, btnNotInt);
    }
}

function createButton(text, isActive, statusId, onClick) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = text;
    if (isActive) btn.classList.add("active");
    if (statusId !== null) btn.dataset.status = statusId; 
    btn.addEventListener("click", onClick);
    return btn;
}

window.rateRecommended = async function(show, status, card) {
    try {
        const res = await fetch("/api/rate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                show: show, 
                status: status
            })
        });

        if (res.status === 401) {
            window.location.href = "/auth";
            return;
        }

        if (res.ok) {
            renderButtons(card, show, status);
        }
    } catch (err) {
        console.error(err);
    }
};