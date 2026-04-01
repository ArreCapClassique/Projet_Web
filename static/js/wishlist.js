async function readJson(res) {
    try {
        return await res.json();
    } catch {
        return {};
    }
}

async function loadWishlist(page = 1) {
    const container = document.getElementById("wishlist-results");
    container.innerHTML = "<p>Loading your wishlist...</p>";

    const res = await fetch(`/api/wishlist?page=${page}`);
    const data = await readJson(res);

    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = "/auth";
            return;
        }
        container.innerHTML = `<p>${data.error || "Failed to load wishlist."}</p>`;
        return;
    }

    renderWishlistResults(data.results);
    renderPagination(data.page, data.pages, loadWishlist, "wishlist-results");
}

function renderWishlistResults(results) {
    const container = document.getElementById("wishlist-results");
    container.innerHTML = "";

    if (!results || results.length === 0) {
        container.innerHTML = "<p>Your wishlist is empty. Try searching for some series!</p>";
        return;
    }

    results.forEach((show, index) => {
        const currentStatus = show.user_status; 
        const card = document.createElement("div");
        card.className = "result-card";

        const buttonGroupId = `buttons-${show.id}-${index}`;

        card.innerHTML = `
            <h3>${show.name}</h3>
            ${show.image ? `<img src="${show.image.medium}" alt="${show.name}">` : ""}
            <div>${show.summary || "<p>No summary available.</p>"}</div>
            <div id="${buttonGroupId}" style="display: flex; flex-wrap: wrap; gap: 8px;">
                <button type="button" class="${currentStatus === '0' ? 'active' : ''}" data-status="0">Like</button>
                <button type="button" class="${currentStatus === '1' ? 'active' : ''}" data-status="1">Neutral</button>
                <button type="button" class="${currentStatus === '2' ? 'active' : ''}" data-status="2">Dislike</button>
                <button type="button" class="${currentStatus === '3' ? 'active' : ''}" data-status="3">Interested</button>
                <button type="button" class="${currentStatus === '4' ? 'active' : ''}" data-status="4">Not Int.</button>
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

function renderPagination(current, totalPages, callback, containerId) {
    let nav = document.getElementById("pagination-controls");
    
    if (!nav) {
        nav = document.createElement("div");
        nav.id = "pagination-controls";
        nav.className = "pagination";
        document.getElementById(containerId).after(nav);
    }

    if (totalPages <= 1) {
        nav.innerHTML = "";
        return;
    }

    nav.innerHTML = `
        <button ${current === 1 ? 'disabled' : ''} id="page-prev">Prev</button>
        <span>Page ${current} of ${totalPages}</span>
        <button ${current === totalPages ? 'disabled' : ''} id="page-next">Next</button>
    `;

    if (current > 1) {
        document.getElementById("page-prev").addEventListener("click", () => callback(current - 1));
    }
    if (current < totalPages) {
        document.getElementById("page-next").addEventListener("click", () => callback(current + 1));
    }
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

document.addEventListener("DOMContentLoaded", () => {
    loadWishlist(1);
});