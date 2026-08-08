(function () {
  "use strict";

  var STORAGE_KEY = "dgh-theme";

  function applyTheme(theme, button) {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    if (button) {
      var isDark = theme === "dark";
      button.setAttribute("aria-pressed", String(isDark));
      button.setAttribute(
        "aria-label",
        isDark ? "Activer le mode clair" : "Activer le mode sombre"
      );
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.querySelector(".dgh-theme-toggle");
    if (!button) {
      return;
    }

    var current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
    applyTheme(current, button);

    button.addEventListener("click", function () {
      current = current === "dark" ? "light" : "dark";
      applyTheme(current, button);
      try {
        localStorage.setItem(STORAGE_KEY, current);
      } catch (e) {
        /* localStorage unavailable (private browsing, quota, etc.) */
      }
    });
  });
})();
