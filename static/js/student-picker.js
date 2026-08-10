(function () {
  var MAX_RESULTS = 12;

  function normalize(text) {
    return (text || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function haystack(entry) {
    return normalize(
      [
        entry.name,
        entry.class_level,
        entry.stream,
        entry.rfid,
        entry.student_code,
        String(entry.id),
        entry.label,
      ].join(" ")
    );
  }

  function initPicker(root) {
    var dataEl = root.querySelector("[data-student-picker-data]");
    var queryInput = root.querySelector("[data-student-picker-query]");
    var valueInput = root.querySelector("[data-student-picker-value]");
    var resultsEl = root.querySelector("[data-student-picker-results]");
    var selectedEl = root.querySelector("[data-student-picker-selected]");
    if (!dataEl || !queryInput || !valueInput || !resultsEl) return;

    var roster;
    try {
      roster = JSON.parse(dataEl.textContent || "[]");
    } catch (e) {
      roster = [];
    }

    var activeIndex = -1;
    var visibleMatches = [];

    function clearSelection() {
      valueInput.value = "";
      if (selectedEl) {
        selectedEl.hidden = true;
        selectedEl.textContent = "";
      }
    }

    function setSelection(entry) {
      valueInput.value = String(entry.id);
      queryInput.value = entry.label;
      if (selectedEl) {
        selectedEl.hidden = false;
        selectedEl.innerHTML =
          '<i class="fa-solid fa-user-check me-1 text-success"></i>Selected: <strong>' +
          entry.label +
          "</strong>";
      }
      closeResults();
      queryInput.setAttribute("aria-expanded", "false");
    }

    function closeResults() {
      resultsEl.hidden = true;
      resultsEl.innerHTML = "";
      activeIndex = -1;
      visibleMatches = [];
    }

    function renderResults(matches) {
      visibleMatches = matches;
      resultsEl.innerHTML = "";
      if (!matches.length) {
        var empty = document.createElement("li");
        empty.className = "list-group-item text-muted small";
        empty.textContent = queryInput.value.trim()
          ? "No learners match your search."
          : "Type to search learners…";
        empty.setAttribute("role", "presentation");
        resultsEl.appendChild(empty);
        resultsEl.hidden = false;
        queryInput.setAttribute("aria-expanded", "true");
        return;
      }

      matches.forEach(function (entry, idx) {
        var li = document.createElement("li");
        li.className = "list-group-item list-group-item-action student-picker-option";
        li.setAttribute("role", "option");
        li.setAttribute("data-index", String(idx));
        li.tabIndex = -1;
        var strong = document.createElement("strong");
        strong.textContent = entry.name;
        var meta = document.createElement("span");
        meta.className = "small text-muted d-block";
        meta.textContent = entry.label;
        li.appendChild(strong);
        li.appendChild(meta);
        li.addEventListener("mousedown", function (e) {
          e.preventDefault();
          setSelection(entry);
        });
        resultsEl.appendChild(li);
      });
      resultsEl.hidden = false;
      queryInput.setAttribute("aria-expanded", "true");
    }

    function filterAndShow() {
      var q = normalize(queryInput.value);
      if (!q) {
        closeResults();
        clearSelection();
        return;
      }

      if (valueInput.value) {
        var current = roster.find(function (r) {
          return String(r.id) === valueInput.value;
        });
        if (current && normalize(current.label) === q) {
          closeResults();
          return;
        }
        clearSelection();
      }

      var tokens = q.split(" ").filter(Boolean);
      var matches = roster.filter(function (entry) {
        var hay = haystack(entry);
        return tokens.every(function (t) {
          return hay.indexOf(t) !== -1;
        });
      });
      renderResults(matches.slice(0, MAX_RESULTS));
    }

    function highlightOption(index) {
      var options = resultsEl.querySelectorAll(".student-picker-option");
      options.forEach(function (el, i) {
        el.classList.toggle("active", i === index);
      });
      activeIndex = index;
      if (index >= 0 && options[index]) {
        options[index].scrollIntoView({ block: "nearest" });
      }
    }

    queryInput.addEventListener("input", filterAndShow);
    queryInput.addEventListener("focus", function () {
      if (queryInput.value.trim() && !valueInput.value) {
        filterAndShow();
      }
    });

    queryInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeResults();
        queryInput.setAttribute("aria-expanded", "false");
        return;
      }
      if (!visibleMatches.length) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        var next = activeIndex + 1;
        if (next >= visibleMatches.length) next = 0;
        highlightOption(next);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        var prev = activeIndex - 1;
        if (prev < 0) prev = visibleMatches.length - 1;
        highlightOption(prev);
      } else if (e.key === "Enter" && activeIndex >= 0) {
        e.preventDefault();
        setSelection(visibleMatches[activeIndex]);
      }
    });

    document.addEventListener("click", function (e) {
      if (!root.contains(e.target)) {
        closeResults();
        queryInput.setAttribute("aria-expanded", "false");
      }
    });

    var form = root.closest("form");
    if (form) {
      form.addEventListener("submit", function (e) {
        if (!valueInput.value) {
          e.preventDefault();
          queryInput.focus();
          filterAndShow();
        }
      });
    }
  }

  function boot() {
    document.querySelectorAll("[data-student-picker]").forEach(initPicker);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
