(() => {
  const root = document.documentElement;
  const loader = document.getElementById("pageLoader");
  const toggle = document.getElementById("themeToggle");
  const sidebar = document.getElementById("appSidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  const searchTrigger = document.getElementById("searchTrigger");
  const searchInput = document.getElementById("searchEverywhereInput");
  const searchResults = document.getElementById("searchEverywhereResults");

  const links = Array.from(document.querySelectorAll("[data-searchable='true']")).map((a) => ({
    label: a.textContent.trim(),
    href: a.getAttribute("href"),
  }));

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("ui-theme", theme);
    if (toggle) {
      toggle.textContent = theme === "dark" ? "Light" : "Dark";
    }
  }

  function initTheme() {
    const stored = localStorage.getItem("ui-theme");
    setTheme(stored || "light");
  }

  function bindSearch() {
    if (!searchInput || !searchResults) {
      return;
    }

    const render = (query) => {
      const q = (query || "").toLowerCase();
      const matched = q ? links.filter((x) => x.label.toLowerCase().includes(q)).slice(0, 8) : [];
      searchResults.innerHTML = matched
        .map((item) => `<a class="list-group-item list-group-item-action" href="${item.href}">${item.label}</a>`)
        .join("");
      if (!matched.length && q) {
        searchResults.innerHTML = '<div class="list-group-item text-muted">No matches</div>';
      }
    };

    searchInput.addEventListener("input", (e) => render(e.target.value));
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    setTimeout(() => loader && loader.classList.add("hidden"), 250);

    if (toggle) {
      toggle.addEventListener("click", () => {
        const current = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
        setTheme(current === "dark" ? "light" : "dark");
      });
    }

    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    }

    if (searchTrigger && searchInput) {
      searchTrigger.addEventListener("click", () => {
        setTimeout(() => searchInput.focus(), 150);
      });
    }

    bindSearch();
  });
})();
