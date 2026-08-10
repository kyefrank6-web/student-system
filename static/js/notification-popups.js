(function () {
  var cfg = window.CAMPUSPASS_LIVE_NOTIF;
  if (!cfg || !cfg.pollUrl) return;

  var STORAGE_KEY = "campuspass_notif_since_" + (cfg.userId || "0");
  var POLL_MS = 8000;
  var container = document.getElementById("live-toast-container");
  if (!container) return;

  var lastId = parseInt(sessionStorage.getItem(STORAGE_KEY) || String(cfg.bootstrapId || 0), 10);
  if (isNaN(lastId)) lastId = cfg.bootstrapId || 0;

  function saveLastId(id) {
    lastId = id;
    sessionStorage.setItem(STORAGE_KEY, String(id));
  }

  function updateBadge(count) {
    var badge = document.getElementById("topbar-notif-badge");
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? "99+" : String(count);
      badge.classList.remove("d-none");
    } else {
      badge.classList.add("d-none");
    }
  }

  function toastMeta(kind) {
    if (kind === "exit_request") {
      return {
        title: "New exit request",
        icon: "fa-clipboard-list",
        accent: "toast-accent-request",
        link: cfg.requestsUrl,
      };
    }
    if (kind === "departure") {
      return {
        title: "Signed out",
        icon: "fa-arrow-right-from-bracket",
        accent: "toast-accent-departure",
        link: cfg.notificationsUrl,
      };
    }
    if (kind === "return") {
      return {
        title: "Signed in",
        icon: "fa-arrow-right-to-bracket",
        accent: "toast-accent-return",
        link: cfg.notificationsUrl,
      };
    }
    if (kind === "request_decision") {
      return {
        title: "Exit request update",
        icon: "fa-clipboard-check",
        accent: "toast-accent-request",
        link: cfg.notificationsUrl,
      };
    }
    if (kind === "school_pending") {
      return {
        title: "School awaiting approval",
        icon: "fa-school",
        accent: "toast-accent-request",
        link: cfg.dashboardUrl || cfg.notificationsUrl,
      };
    }
    return {
      title: "CampusPass",
      icon: "fa-bell",
      accent: "",
      link: cfg.notificationsUrl,
    };
  }

  function showToast(item) {
    var meta = toastMeta(item.kind);
    var el = document.createElement("div");
    el.className = "live-toast " + meta.accent;
    el.setAttribute("role", "alert");
    el.innerHTML =
      '<div class="live-toast-icon"><i class="fa-solid ' +
      meta.icon +
      '"></i></div>' +
      '<div class="live-toast-body">' +
      '<div class="live-toast-title">' +
      escapeHtml(meta.title) +
      (item.created_at ? ' <span class="live-toast-time">' + escapeHtml(item.created_at) + "</span>" : "") +
      "</div>" +
      '<div class="live-toast-msg">' +
      escapeHtml(item.message) +
      "</div>" +
      (meta.link
        ? '<a href="' +
          meta.link +
          '" class="live-toast-link">View details <i class="fa-solid fa-arrow-right ms-1"></i></a>'
        : "") +
      "</div>" +
      '<button type="button" class="live-toast-close" aria-label="Dismiss">&times;</button>';

    el.querySelector(".live-toast-close").addEventListener("click", function () {
      dismiss(el);
    });

    container.appendChild(el);
    requestAnimationFrame(function () {
      el.classList.add("live-toast-show");
    });

    var timer = setTimeout(function () {
      dismiss(el);
    }, 12000);

    el.addEventListener("mouseenter", function () {
      clearTimeout(timer);
    });
    el.addEventListener("mouseleave", function () {
      timer = setTimeout(function () {
        dismiss(el);
      }, 4000);
    });
  }

  function dismiss(el) {
    el.classList.remove("live-toast-show");
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 300);
  }

  function escapeHtml(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function poll() {
    fetch(cfg.pollUrl + "?since_id=" + encodeURIComponent(lastId), {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    })
      .then(function (r) {
        if (!r.ok) throw new Error("poll failed");
        return r.json();
      })
      .then(function (data) {
        if (typeof data.unread_count === "number") {
          updateBadge(data.unread_count);
        }
        var list = data.notifications || [];
        list.forEach(function (item) {
          if (item.id > lastId) {
            showToast(item);
            saveLastId(item.id);
          }
        });
        if (list.length) {
          var maxId = list.reduce(function (m, n) {
            return n.id > m ? n.id : m;
          }, lastId);
          if (maxId > lastId) saveLastId(maxId);
        }
      })
      .catch(function () {});
  }

  if (!sessionStorage.getItem(STORAGE_KEY)) {
    saveLastId(cfg.bootstrapId || 0);
  }

  poll();
  setInterval(poll, POLL_MS);
})();
