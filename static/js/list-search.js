(function () {
  function normalize(text) {
    return (text || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function initPanel(panel) {
    var input = panel.querySelector("[data-list-search-input]");
    if (!input) return;

    var rows = panel.querySelectorAll("[data-search-text]");
    var items = panel.querySelectorAll("[data-search-item]");
    var targets = rows.length ? rows : items;
    if (!targets.length) return;

    var meta = panel.querySelector("[data-list-search-meta]");
    var emptyEl = panel.querySelector("[data-list-search-empty]");
    var clearBtn = panel.querySelector("[data-list-search-clear]");
    var total = targets.length;

    function setMeta(visible) {
      if (!meta) return;
      var q = input.value.trim();
      if (!q) {
        meta.textContent = total + (total === 1 ? " record" : " records");
        return;
      }
      meta.textContent =
        "Showing " +
        visible +
        " of " +
        total +
        (visible === 1 ? " match" : " matches");
    }

    function applyFilter() {
      var q = normalize(input.value);
      var visible = 0;

      targets.forEach(function (el) {
        var hay = normalize(el.getAttribute("data-search-text") || el.textContent);
        var show = !q || hay.indexOf(q) !== -1;
        el.classList.toggle("list-search-hidden", !show);
        if (show) visible += 1;
      });

      if (clearBtn) {
        clearBtn.classList.toggle("d-none", !q);
      }
      if (emptyEl) {
        emptyEl.classList.toggle("d-none", visible > 0 || !q);
      }
      setMeta(visible);
    }

    input.addEventListener("input", applyFilter);
    input.addEventListener("search", applyFilter);

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        input.value = "";
        input.focus();
        applyFilter();
      });
    }

    applyFilter();
  }

  function boot() {
    document.querySelectorAll("[data-list-search-panel]").forEach(initPanel);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
