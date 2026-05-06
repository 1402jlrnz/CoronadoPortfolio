const mobileMenuButton = document.getElementById("mobile-menu");
const navMenu = document.querySelector(".nav-menu");

if (mobileMenuButton && navMenu) {
    mobileMenuButton.addEventListener("click", () => {
        navMenu.classList.toggle("active");
    });
}

document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
        navMenu?.classList.remove("active");
    });
});

document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (event) => {
        const targetId = anchor.getAttribute("href");
        if (!targetId || targetId === "#") {
            return;
        }
        const target = document.querySelector(targetId);
        if (!target) {
            return;
        }
        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
});
