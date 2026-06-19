(function () {
  var STORAGE_KEY = "secureflow-theme";

  function preferredTheme() {
    var saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      var icon = btn.querySelector("[data-theme-icon]");
      var label = btn.querySelector("[data-theme-label]");
      var isDark = theme === "dark";
      if (icon) {
        icon.className = isDark ? "ti ti-sun" : "ti ti-moon";
      }
      if (label) {
        label.textContent = isDark ? "Clair" : "Sombre";
      }
      btn.setAttribute("aria-label", isDark ? "Activer le mode clair" : "Activer le mode sombre");
      btn.setAttribute("title", isDark ? "Mode clair" : "Mode sombre");
    });
  }

  window.SecureFlowTheme = {
    get: function () {
      return document.documentElement.getAttribute("data-theme") || "dark";
    },
    set: applyTheme,
    toggle: function () {
      applyTheme(this.get() === "dark" ? "light" : "dark");
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(preferredTheme());
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        window.SecureFlowTheme.toggle();
      });
    });
  });
})();
