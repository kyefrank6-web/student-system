(function () {
  var form = document.getElementById("login-form");
  if (!form) return;

  var fields = form.querySelectorAll("[data-login-field]");

  function clearFields() {
    fields.forEach(function (el) {
      el.value = "";
    });
  }

  function armField(el) {
    el.setAttribute("readonly", "readonly");
    el.setAttribute("autocomplete", "off");
    el.value = "";
    el.addEventListener(
      "focus",
      function onFocus() {
        el.removeAttribute("readonly");
      },
      { once: true }
    );
  }

  fields.forEach(armField);
  clearFields();

  // Browsers often apply autofill after DOMContentLoaded.
  window.setTimeout(clearFields, 0);
  window.setTimeout(clearFields, 100);
  window.setTimeout(clearFields, 500);

  form.addEventListener("submit", function () {
    fields.forEach(function (el) {
      el.removeAttribute("readonly");
    });
  });
})();
