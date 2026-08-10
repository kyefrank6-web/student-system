(function () {
  function initInput(input) {
    var targetId = input.getAttribute("data-photo-preview-target");
    if (!targetId) return;
    var preview = document.getElementById(targetId);
    if (!preview) return;

    input.addEventListener("change", function () {
      var file = input.files && input.files[0];
      if (!file || !file.type.match(/^image\//)) return;

      var reader = new FileReader();
      reader.onload = function () {
        if (preview.tagName === "IMG") {
          preview.src = reader.result;
          return;
        }
        var img = document.createElement("img");
        img.id = targetId;
        img.className = "learner-photo-preview";
        img.alt = "Photo preview";
        img.src = reader.result;
        preview.replaceWith(img);
      };
      reader.readAsDataURL(file);
    });
  }

  function boot() {
    document
      .querySelectorAll("[data-photo-preview-target]")
      .forEach(initInput);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
