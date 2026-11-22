document.querySelectorAll("[data-task-composer]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (form.dataset.sending) { event.preventDefault(); return; }
    form.dataset.sending = "true";
    const button = form.querySelector("[data-send-button]");
    const status = form.querySelector("[data-sending]");
    button.disabled = true;
    status.hidden = false;
  });
});
