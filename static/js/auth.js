const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

const toRegisterButton = document.getElementById("toRegister");
const toLoginButton = document.getElementById("toLogin");

async function readJson(res) {
    try {
        return await res.json();
    } catch {
        return {};
    }
}

if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = document.getElementById("login-username").value.trim();
        const password = document.getElementById("login-password").value;

        try {
            const res = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await readJson(res);

            if (!res.ok) {
                alert(data.error || `HTTP ${res.status}`);
                return;
            }

            window.location.href = "/";
        } catch (err) {
            console.error(err);
            alert("Une erreur réseau est survenue.");
        }
    });
}

if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = document.getElementById("register-username").value.trim();
        const password = document.getElementById("register-password").value;

        try {
            const res = await fetch("/api/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await readJson(res);

            if (!res.ok) {
                alert(data.error || `HTTP ${res.status}`);
                return;
            }

            window.location.href = "/";
        } catch (err) {
            console.error(err);
            alert("Une erreur réseau est survenue.");
        }
    });
}

if (toRegisterButton) {
    toRegisterButton.addEventListener("click", () => {
        loginForm.classList.add("hidden");
        registerForm.classList.remove("hidden");
    });
}

if (toLoginButton) {
    toLoginButton.addEventListener("click", () => {
        registerForm.classList.add("hidden");
        loginForm.classList.remove("hidden");
    });
}