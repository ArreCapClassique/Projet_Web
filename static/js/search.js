async function readJson(res) {
    try {
        return await res.json();
    } catch {
        return {};
    }
}

document.getElementById("searchForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const query = document.getElementById("query").value.trim();

    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await readJson(res);

    renderResults(data);
});

function renderResults(results) {
    const container = document.getElementById("results");
    container.innerHTML = "";

    if (!results || results.length === 0) {
        container.innerHTML = "<p>No results found.</p>";
        return;
    }

    results.forEach((result, index) => {
        const show = result.show;
        const card = document.createElement("div");
        card.className = "result-card";

        const buttonGroupId = `buttons-${show.id}-${index}`;

        card.innerHTML = `
            <h3>${show.name}</h3>
            ${show.image ? `<img src="${show.image.medium}" alt="${show.name}">` : ""}
            <div>${show.summary || "<p>No summary available.</p>"}</div>
            <div id="${buttonGroupId}">
                <button type="button" data-rating="1">Aimé</button>
                <button type="button" data-rating="0">Neutre</button>
                <button type="button" data-rating="-1">N’aime pas</button>
            </div>
        `;

        container.appendChild(card);

        const buttons = card.querySelectorAll("button[data-rating]");
        buttons.forEach((button) => {
            button.addEventListener("click", async () => {
                await rate(show, button.dataset.rating);
            });
        });
    });
}

async function rate(show, rating) {
    await fetch("/api/rate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            show: show,
            rating: rating
        })
    });
}