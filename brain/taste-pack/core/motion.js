(() => {
  const root = document.documentElement;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(pointer: fine)").matches;
  root.classList.add("js");

  const nav = document.querySelector("[data-nav]");
  if (nav) {
    const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    const toggle = nav.querySelector("[data-nav-toggle]");
    const menu = nav.querySelector(".nav__menu");
    if (toggle && menu) {
      const setOpen = (open) => {
        toggle.setAttribute("aria-expanded", String(open));
        menu.classList.toggle("is-open", open);
      };
      toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
      menu.addEventListener("click", (event) => {
        if (event.target.closest("a")) setOpen(false);
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") setOpen(false);
      });
    }
  }

  const groups = new Map();
  document.querySelectorAll("[data-reveal]").forEach((el) => {
    const parent = el.parentElement;
    const index = groups.get(parent) || 0;
    el.style.setProperty("--reveal-i", String(Math.min(index, 6)));
    groups.set(parent, index + 1);
  });

  const countUp = (el) => {
    const target = Number(el.dataset.count);
    if (!Number.isFinite(target)) return;
    const decimals = (el.dataset.count.split(".")[1] || "").length;
    const prefix = el.dataset.prefix || "";
    const suffix = el.dataset.suffix || "";
    const format = (value) => prefix + value.toLocaleString("id-ID", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix;
    if (reduced) {
      el.textContent = format(target);
      return;
    }
    const duration = 1400;
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4);
      el.textContent = format(target * eased);
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  const typeTerminal = (body) => {
    const lines = Array.from(body.querySelectorAll(".terminal__line"));
    if (reduced || !lines.length) return;
    const texts = lines.map((line) => line.textContent);
    lines.forEach((line) => {
      line.textContent = "";
      line.hidden = true;
    });
    const cursor = document.createElement("span");
    cursor.className = "terminal__cursor";
    cursor.setAttribute("aria-hidden", "true");
    let i = 0;
    const next = () => {
      if (i >= lines.length) {
        lines[lines.length - 1].after(cursor);
        return;
      }
      const line = lines[i];
      const text = texts[i];
      line.hidden = false;
      line.after(cursor);
      if (line.classList.contains("terminal__line--cmd")) {
        let c = 0;
        const typeChar = () => {
          line.textContent = text.slice(0, ++c);
          if (c < text.length) setTimeout(typeChar, 22 + Math.random() * 30);
          else setTimeout(() => { i += 1; next(); }, 380);
        };
        typeChar();
      } else {
        line.textContent = text;
        i += 1;
        setTimeout(next, 160);
      }
    };
    next();
  };

  if (!reduced) {
    document.querySelectorAll("[data-count]").forEach((el) => {
      el.textContent = (el.dataset.prefix || "") + "0" + (el.dataset.suffix || "");
    });
  }

  const onVisible = (el) => {
    el.classList.add("is-visible");
    if (el.matches("[data-count]")) countUp(el);
    if (el.matches("[data-terminal]")) typeTerminal(el);
  };

  const watched = document.querySelectorAll("[data-reveal], [data-terminal], .steps__item, [data-count]");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        onVisible(entry.target);
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.15 });
    watched.forEach((el) => observer.observe(el));
  } else {
    watched.forEach(onVisible);
  }

  if (finePointer && !reduced) {
    document.querySelectorAll(".bento__card").forEach((card) => {
      card.addEventListener("pointermove", (event) => {
        const rect = card.getBoundingClientRect();
        card.style.setProperty("--mx", `${event.clientX - rect.left}px`);
        card.style.setProperty("--my", `${event.clientY - rect.top}px`);
      });
    });
    document.querySelectorAll("[data-magnetic]").forEach((btn) => {
      btn.addEventListener("pointermove", (event) => {
        const rect = btn.getBoundingClientRect();
        const x = (event.clientX - rect.left - rect.width / 2) * 0.18;
        const y = (event.clientY - rect.top - rect.height / 2) * 0.3;
        btn.style.setProperty("--btn-x", `${x}px`);
        btn.style.setProperty("--btn-y", `${y}px`);
      });
      btn.addEventListener("pointerleave", () => {
        btn.style.setProperty("--btn-x", "0px");
        btn.style.setProperty("--btn-y", "0px");
      });
    });
  }

  document.querySelectorAll("[data-tabs]").forEach((tabs) => {
    const buttons = Array.from(tabs.querySelectorAll("[role='tab']"));
    const select = (button, focus) => {
      buttons.forEach((b) => {
        const active = b === button;
        b.setAttribute("aria-selected", String(active));
        b.tabIndex = active ? 0 : -1;
        const panel = document.getElementById(b.getAttribute("aria-controls"));
        if (!panel) return;
        panel.hidden = !active;
        if (active && !reduced) {
          panel.classList.remove("is-entering");
          void panel.offsetWidth;
          panel.classList.add("is-entering");
        }
      });
      if (focus) button.focus();
    };
    buttons.forEach((button, index) => {
      button.addEventListener("click", () => select(button, false));
      button.addEventListener("keydown", (event) => {
        const keys = { ArrowRight: 1, ArrowLeft: -1 };
        if (event.key in keys) {
          event.preventDefault();
          select(buttons[(index + keys[event.key] + buttons.length) % buttons.length], true);
        } else if (event.key === "Home") {
          event.preventDefault();
          select(buttons[0], true);
        } else if (event.key === "End") {
          event.preventDefault();
          select(buttons[buttons.length - 1], true);
        }
      });
    });
  });

  document.querySelectorAll("[data-pricing]").forEach((pricing) => {
    const options = pricing.querySelectorAll("[data-period]");
    options.forEach((option) => {
      option.addEventListener("click", () => {
        const period = option.dataset.period;
        options.forEach((o) => o.setAttribute("aria-pressed", String(o === option)));
        pricing.querySelectorAll("[data-monthly]").forEach((amount) => {
          amount.textContent = period === "yearly" ? amount.dataset.yearly : amount.dataset.monthly;
        });
        pricing.querySelectorAll("[data-period-label]").forEach((label) => {
          label.textContent = period === "yearly" ? label.dataset.yearlyLabel : label.dataset.monthlyLabel;
        });
      });
    });
  });
})();
