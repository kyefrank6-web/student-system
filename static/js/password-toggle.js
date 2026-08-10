(function () {
  function initPasswordToggles(root) {
    var scope = root || document;
    scope.querySelectorAll(".password-input-wrap").forEach(function (wrap) {
      if (wrap.dataset.toggleInit) return;
      wrap.dataset.toggleInit = "1";

      var input = wrap.querySelector(".password-input, input[type='password']");
      var btn = wrap.querySelector(".password-toggle-btn");
      if (!input || !btn) return;

      var icon = btn.querySelector("i");

      btn.addEventListener("click", function () {
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        if (icon) {
          icon.classList.toggle("fa-eye", show);
          icon.classList.toggle("fa-eye-slash", !show);
        }
        btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
        btn.title = show ? "Hide password" : "Show password";
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initPasswordToggles();
    });
  } else {
    initPasswordToggles();
  }

  window.initPasswordToggles = initPasswordToggles;
})();
