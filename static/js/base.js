document.addEventListener("DOMContentLoaded", () => {

    const logoutBtn = document.getElementById("nav-logout-btn");

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                await fetch("/api/logout", { method: "POST" });
                window.location.href = "/";
            } catch (err) {
                console.error("Logout failed", err);
            }
        });
    }
});

window.openTvmaze = function (showId) {
    if (!showId) return;
    const url = `https://www.tvmaze.com/shows/${showId}`;
    window.open(url, "_blank");
};