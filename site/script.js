(function () {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const revealElements = document.querySelectorAll(".reveal");
  const counterElements = document.querySelectorAll("[data-counter]");
  const tiltCards = document.querySelectorAll(".tilt-card");
  const yearElement = document.getElementById("year");

  if (yearElement) {
    yearElement.textContent = String(new Date().getFullYear());
  }

  const animatedCounters = new WeakSet();

  function animateCounter(el) {
    if (animatedCounters.has(el)) {
      return;
    }
    animatedCounters.add(el);

    const target = Number(el.getAttribute("data-counter") || 0);
    const duration = 1300;
    const startTime = performance.now();

    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(target * eased).toLocaleString();
      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    }

    requestAnimationFrame(tick);
  }

  if (!prefersReducedMotion && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }

          const el = entry.target;
          const delay = Number(el.getAttribute("data-delay") || 0);
          window.setTimeout(() => {
            el.classList.add("visible");
          }, delay);

          el.querySelectorAll("[data-counter]").forEach((counter) => animateCounter(counter));
          if (el.hasAttribute("data-counter")) {
            animateCounter(el);
          }

          observer.unobserve(el);
        });
      },
      { threshold: 0.2 }
    );

    revealElements.forEach((el) => observer.observe(el));
    counterElements.forEach((el) => observer.observe(el));
  } else {
    revealElements.forEach((el) => el.classList.add("visible"));
    counterElements.forEach((el) => animateCounter(el));
  }

  if (!prefersReducedMotion) {
    tiltCards.forEach((card) => {
      card.addEventListener("mousemove", (event) => {
        const rect = card.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width;
        const y = (event.clientY - rect.top) / rect.height;

        const rotateY = (x - 0.5) * 10;
        const rotateX = (0.5 - y) * 8;

        card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-2px)`;
      });

      card.addEventListener("mouseleave", () => {
        card.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0px)";
      });
    });

    const bgLayer = document.querySelector(".bg-layer");
    if (bgLayer) {
      window.addEventListener("mousemove", (event) => {
        const x = (event.clientX / window.innerWidth - 0.5) * 8;
        const y = (event.clientY / window.innerHeight - 0.5) * 8;
        bgLayer.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      });
    }
  }

  const passwordInput = document.getElementById("password");
  const passwordToggle = document.getElementById("passwordToggle");
  if (passwordInput && passwordToggle) {
    passwordToggle.addEventListener("click", () => {
      const isPassword = passwordInput.getAttribute("type") === "password";
      passwordInput.setAttribute("type", isPassword ? "text" : "password");
      passwordToggle.textContent = isPassword ? "Hide" : "Show";
    });
  }

  const authForm = document.getElementById("authForm");
  const formFeedback = document.getElementById("formFeedback");
  if (authForm && formFeedback) {
    authForm.addEventListener("submit", (event) => {
      event.preventDefault();
      formFeedback.textContent = "Authenticating securely...";

      window.setTimeout(() => {
        formFeedback.textContent = "Demo login successful. Connect your backend auth provider next.";
      }, 900);
    });
  }
})();
