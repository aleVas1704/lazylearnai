document.querySelectorAll("[data-task-composer]").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("[data-send-button]");
    const status = form.querySelector("[data-sending]");
    button.disabled = true;
    status.hidden = false;
  });
});
