async function readJson(res) {
    try {
        return await res.json();
    } catch {
        return {};
    }
}

async function performSearch(query) {
    const container = document.getElementById("results");

    if (!query) {
        container.innerHTML = "<p>No query provided.</p>";
        return;
    }

    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await readJson(res);

    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = "/auth";
            return;
        }
        container.innerHTML = `<p>${data.error || "Search failed."}</p>`;
        return;
    }

    renderResults(data);
}

function renderResults(results) {
    const container = document.getElementById("results");
    container.innerHTML = "";

    if (!results || results.length === 0) {
        container.innerHTML = "<p>No results found.</p>";
        return;
    }

    results.forEach((result, index) => {
        const show = result.show;
        const currentStatus = show.user_status; 
        const card = document.createElement("div");
        card.className = "result-card";

        const buttonGroupId = `buttons-${show.id}-${index}`;


        card.innerHTML = `
            <h3>${show.name}</h3>
            ${show.image ? `<img src="${show.image.medium}" alt="${show.name}">` : ""}
            <div>${show.summary || "<p>No summary available.</p>"}</div>
            <div id="${buttonGroupId}">
                <button type="button" class="${currentStatus === '0' ? 'active' : ''}" data-status="0">Like</button>
                <button type="button" class="${currentStatus === '1' ? 'active' : ''}" data-status="1">Neutral</button>
                <button type="button" class="${currentStatus === '2' ? 'active' : ''}" data-status="2">Dislike</button>
            </div>
        `;

        container.appendChild(card);

        const buttons = card.querySelectorAll("button[data-status]");
        buttons.forEach((button) => {
            button.addEventListener("click", async () => {
                const status = button.dataset.status;
                
                const res = await rate(show, status);

                if (res && res.ok) {
                    buttons.forEach(btn => btn.classList.remove("active"));
                    button.classList.add("active");
                } else if (res && res.status === 401) {
                    window.location.href = "/auth";
                }
            });
        });
    });
}

async function rate(show, status) {
    return await fetch("/api/rate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            show: show,
            status: status 
        })
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    const query = (params.get("q") || "").trim();

    await performSearch(query);
});