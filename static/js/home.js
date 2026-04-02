document.addEventListener("DOMContentLoaded", async () => {
    await loadRecommendations();
});

async function loadRecommendations() {
    const container = document.getElementById("recommendations");
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
        const safeShowName = show.name.replace(/'/g, "\\'");
        
        const currentStatus = show.user_status;

        card.innerHTML = `
            <h3>${show.name}</h3>
            ${show.image ? `<img src="${show.image.medium}" alt="${show.name}">` : ""}
            <div id="action-buttons-${show.id}" class="action-buttons">
                ${renderButtons(show.id, safeShowName, currentStatus)}
            </div>
        `;
        container.appendChild(card);
    });
}
function renderButtons(showId, showName, status) {

    if (["0", "1", "2"].includes(status)) {
        return `
            <button type="button" class="${status === '0' ? 'active' : ''}" data-status="0" onclick="rateRecommended(${showId}, '${showName}', '0')">Like</button>
            <button type="button" class="${status === '1' ? 'active' : ''}" data-status="1" onclick="rateRecommended(${showId}, '${showName}', '1')">Neutral</button>
            <button type="button" class="${status === '2' ? 'active' : ''}" data-status="2" onclick="rateRecommended(${showId}, '${showName}', '2')">Dislike</button>
        `;
    }
  
    return `
        <button type="button" onclick="showWatchedOptions(${showId}, '${showName}')">Watched</button>
        <button type="button" class="${status === '3' ? 'active' : ''}" data-status="3" onclick="rateRecommended(${showId}, '${showName}', '3')">Interested</button>
        <button type="button" class="${status === '4' ? 'active' : ''}" data-status="4" onclick="rateRecommended(${showId}, '${showName}', '4')">Not Interested</button>
    `;
}

window.showWatchedOptions = function(showId, showName) {
    const actionDiv = document.getElementById(`action-buttons-${showId}`);
    actionDiv.innerHTML = renderButtons(showId, showName, "0");
};

window.rateRecommended = async function(showId, showName, status) {
    try {
        const res = await fetch("/api/rate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                show: { id: showId, name: showName },
                status: status
            })
        });

        if (res.status === 401) {
            window.location.href = "/auth";
            return;
        }

        if (res.ok) {
            const actionDiv = document.getElementById(`action-buttons-${showId}`);
            actionDiv.innerHTML = renderButtons(showId, showName, status);
        }
    } catch (err) {
        console.error(err);
    }
};