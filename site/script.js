// Scroll Reveal Animation
document.addEventListener("DOMContentLoaded", function () {
    const reveals = document.querySelectorAll(".reveal");

    const revealOnScroll = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("active");
                observer.unobserve(entry.target);
            }
        });
    }, {

        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    });

    reveals.forEach(reveal => {
        revealOnScroll.observe(reveal);
    });

    // Hover Glowing Effect for Cards
    const cards = document.querySelectorAll(".hover-glowing");
    cards.forEach(card => {
        card.addEventListener("mousemove", e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            card.style.setProperty("--x", `${x}px`);
            card.style.setProperty("--y", `${y}px`);
        });
    });

    // Add sticky class to navbar on scroll
    const navbar = document.querySelector(".navbar");
    window.addEventListener("scroll", () => {
        if (window.scrollY > 50) {
            navbar.style.background = "rgba(8, 8, 12, 0.85)";
            navbar.style.boxShadow = "0 4px 30px rgba(0, 0, 0, 0.1)";
        } else {
            navbar.style.background = "rgba(8, 8, 12, 0.7)";
            navbar.style.boxShadow = "none";
        }
    });

    // Smooth Scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Copy to Clipboard logic for quick start
function copyCode(button) {
    const codeBlock = button.previousElementSibling;
    const textToCopy = codeBlock.textContent;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const icon = button.querySelector("i");
        // Change to check icon
        icon.className = "fa-solid fa-check";
        icon.style.color = "#4ade80"; // green

        // Revert back after 2s
        setTimeout(() => {
            icon.className = "fa-regular fa-copy";
            icon.style.color = "";
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}
