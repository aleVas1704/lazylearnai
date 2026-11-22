(() => {
  const sections = document.querySelectorAll("[data-teacher-section]");
  const tabs = document.querySelectorAll("[data-teacher-tab]");
  const get = (id) => document.getElementById(id);
  const show = (tab) => {
    sections.forEach((node) => { node.hidden = node.dataset.teacherSection !== tab; });
    tabs.forEach((node) => {
      node.classList.toggle("is-active", node.dataset.teacherTab === tab);
      node.setAttribute("aria-selected", String(node.dataset.teacherTab === tab));
    });
  };
  tabs.forEach((node) => node.addEventListener("click", () => show(node.dataset.teacherTab)));
  document.querySelectorAll("[data-choose-class]").forEach((node) => {
    node.addEventListener("click", () => {
      get("teacher-class").value = node.dataset.chooseClass;
      show("tareas");
    });
  });

  const status = (id, text, error = false) => {
    const node = get(id);
    node.textContent = text;
    node.classList.toggle("is-error", error);
  };
  const jsonPost = async (url, data) => {
    const res = await fetch(url, {
      method: "POST", headers: { "Content-Type": "application/json" },
      credentials: "same-origin", body: JSON.stringify(data),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || `Error ${res.status}`);
    return body;
  };
  const uploadAsBase64 = async (file) => {
    const buf = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (let i = 0; i < buf.length; i += 8192) {
      binary += String.fromCharCode(...buf.slice(i, i + 8192));
    }
    return btoa(binary);
  };
  let preview = null;
  let currentGroup = null;
  let currentFileName = null;
  let publicationId = null;
  get("teacher-mcm-draft").addEventListener("click", () => {
    const a = Number(get("mcm-a").value), b = Number(get("mcm-b").value);
    const group = get("teacher-class").value;
    if (!group || ![a, b].every(n => Number.isInteger(n) && n >= 1 && n <= 100)) {
      return status("teacher-generate-status", "Elige tu clase y dos enteros entre 1 y 100.", true);
    }
    preview = { task_type: "mcm", exercises: [{a, b}] };
    publicationId = crypto.randomUUID();
    currentGroup = group;
    currentFileName = null;
    get("teacher-draft-title").value = `Mínimo común múltiplo de ${a} y ${b}`;
    get("teacher-draft-description").value = "Encuentra el mínimo común múltiplo. Puedes preguntar cuando lo necesites.";
    const li = document.createElement("li");
    li.textContent = `¿Cuál es el MCM de ${a} y ${b}?`;
    get("teacher-draft-exercises").replaceChildren(li);
    get("teacher-preview-card").hidden = false;
    get("teacher-publish-button").disabled = false;
    status("teacher-generate-status", "Revisa la actividad antes de publicarla.");
  });

  get("teacher-generate-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const group_key = get("teacher-class").value;
    const instructions = get("teacher-instructions").value.trim();
    const file = get("teacher-material").files[0];
    const btn = get("teacher-generate-button");
    if (!group_key) return status("teacher-generate-status", "Selecciona una clase", true);
    if (file && file.size > 3 * 1024 * 1024) return status("teacher-generate-status", "Archivo mayor a 3 MB", true);
    btn.disabled = true;
    status("teacher-generate-status", "Gemini está preparando la tarea…");
    get("teacher-preview-card").hidden = true;
    try {
      const data = { group_key, instructions, filename: file?.name ?? null,
        file_base64: file ? await uploadAsBase64(file) : null };
      preview = await jsonPost("/teacher/tasks/generate", data);
      publicationId = crypto.randomUUID();
      get("teacher-publish-button").disabled = false;
      currentGroup = group_key;
      currentFileName = file?.name ?? null;
      get("teacher-draft-title").value = preview.title;
      get("teacher-draft-description").value = preview.description;
      const list = get("teacher-draft-exercises");
      list.replaceChildren();
      preview.exercises.forEach((ex) => {
        const li = document.createElement("li");
        li.textContent = `${ex.a_num}/${ex.a_den} ${ex.operator} ${ex.b_num}/${ex.b_den}`;
        list.append(li);
      });
      get("teacher-preview-card").hidden = false;
      status("teacher-generate-status", "Borrador generado. Revísalo antes de publicar.");
    } catch (err) {
      status("teacher-generate-status", err.message, true);
    } finally { btn.disabled = false; }
  });
  get("teacher-publish-button").addEventListener("click", async () => {
    if (!preview) return;
    const btn = get("teacher-publish-button");
    btn.disabled = true;
    status("teacher-publish-status", "Publicando tarea…");
    try {
      const result = await jsonPost("/teacher/tasks/publish", {
        group_key: currentGroup, filename: currentFileName,
        title: get("teacher-draft-title").value,
        description: get("teacher-draft-description").value,
        exercises: preview.exercises,
        task_type: preview.task_type || "fraction_add_sub", publication_id: publicationId,
      });
      status("teacher-publish-status", `Tarea #${result.task_id} publicada. Ya aparece a estudiantes del grupo.`);
      preview = null;
      btn.disabled = true;
    } catch (err) {
      status("teacher-publish-status", err.message, true);
      btn.disabled = false;
    }
  });

  const modal = get("teacher-report-modal");
  const close = () => { modal.hidden = true; };
  get("teacher-modal-close").addEventListener("click", close);
  modal.addEventListener("click", (e) => { if (e.target === modal) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  document.querySelectorAll("[data-report-task]").forEach((button) => {
    button.addEventListener("click", async () => {
      const taskId = button.dataset.reportTask;
      const studentId = button.dataset.reportStudent;
      get("teacher-modal-subtitle").textContent = "Cargando historial…";
      get("teacher-chat-history").replaceChildren();
      get("teacher-report-events").replaceChildren();
      get("teacher-summary-text").textContent = "Resumen opcional para el docente.";
      modal.hidden = false;
      try {
        const response = await fetch(`/teacher/report/${taskId}/${studentId}`, { credentials: "same-origin" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "No disponible");
        get("teacher-modal-subtitle").textContent = `${data.student} · ${data.title} · ${data.completed ? "Completada" : "En progreso"} ${data.completed_count}/${data.total_exercises}`;
        const events = data.events.filter((ev) => ["paste", "answer_request", "tab_hidden"].includes(ev.kind));
        const summary = document.createElement("p");
        summary.className = "teacher-note";
        summary.textContent = `Señales registradas: ${events.length}. No son pruebas de deshonestidad.`;
        get("teacher-report-events").append(summary);
        events.forEach((ev) => {
          const line = document.createElement("p");
          line.className = "teacher-note";
          const label = {paste: "Pegado detectado", tab_hidden: "Pestaña oculta",
            answer_request: "Pidió la respuesta final"}[ev.kind];
          line.textContent = `${label} · ejercicio ${ev.exercise_index ?? "?"} · ${new Date(ev.at).toLocaleTimeString("es-BO")}`;
          get("teacher-report-events").append(line);
        });
        data.messages.forEach((msg) => {
          const node = document.createElement("div");
          node.className = `teacher-chat-message ${msg.role === "student" ? "student" : ""}`;
          const label = document.createElement("small");
          label.textContent = msg.role === "student" ? "Estudiante" : "Tutor guiado";
          const text = document.createElement("div");
          text.textContent = msg.text;
          node.append(label, text);
          get("teacher-chat-history").append(node);
        });
        get("teacher-summary-button").onclick = async () => {
          const b = get("teacher-summary-button");
          b.disabled = true;
          get("teacher-summary-text").textContent = "Gemini está redactando el resumen…";
          try {
            const output = await jsonPost(`/teacher/report/${taskId}/${studentId}/summary`, {});
            get("teacher-summary-text").textContent = output.summary;
          } catch (err) { get("teacher-summary-text").textContent = err.message; }
          finally { b.disabled = false; }
        };
      } catch (err) { get("teacher-modal-subtitle").textContent = err.message; }
    });
  });
})();
