/* Señales del navegador: informativas, no evidencia de fraude.
   No registra contenido pegado, teclado, direcciones ni otras pestañas. */
(() => {
  const form = document.querySelector("[data-guided-task]");
  if (!form) return;
  const taskId = form.dataset.guidedTask;
  const activity = (kind) => {
    fetch(`/student/tasks/${encodeURIComponent(taskId)}/activity`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind }),
      keepalive: true,
    }).catch(() => {});
  };
  form.addEventListener("paste", (ev) => {
    if (ev.target.closest("textarea")) activity("paste");
  });
  document.addEventListener("visibilitychange", () => {
    activity(document.hidden ? "tab_hidden" : "tab_visible");
  });
})();
