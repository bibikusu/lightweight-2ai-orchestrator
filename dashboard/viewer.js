(function () {
  "use strict";
  const PATHS = {
    projectsYaml: "../docs/projects.yaml",
    queueState: "../queue_state.json"
  };
  const STATUS_META = {
    idle: { icon: "⚪", label: "idle", className: "status-idle" },
    running: { icon: "🟢", label: "running", className: "status-running" },
    waiting: { icon: "🟡", label: "waiting", className: "status-waiting" },
    blocked: { icon: "🔴", label: "blocked", className: "status-blocked" },
    completed: { icon: "✅", label: "completed", className: "status-completed" },
    error: { icon: "❌", label: "error", className: "status-error" }
  };
  function setGlobalMessage(message, kind) {
    const box = document.getElementById("global-message");
    if (!message) {
      box.innerHTML = "";
      return;
    }
    const className = kind === "error" ? "error-banner" : "loading";
    box.innerHTML = `<div class="${className}">${escapeHtml(message)}</div>`;
  }
  function updateLastUpdated(text) {
    const label = document.getElementById("last-updated-label");
    label.textContent = `最終更新: ${text}`;
  }
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
  async function fetchText(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`${url} の取得に失敗しました (${response.status})`);
    }
    return await response.text();
  }
  async function fetchJson(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`${url} の取得に失敗しました (${response.status})`);
    }
    return await response.json();
  }
  async function tryFetchJson(url) {
    try {
      return await fetchJson(url);
    } catch (error) {
      return null;
    }
  }
  function normalizeProjectsYaml(doc) {
    if (!doc || !Array.isArray(doc.projects)) {
      throw new Error("docs/projects.yaml の形式が不正です");
    }
    return doc.projects.map((project) => ({
      id: project.id,
      name: project.name,
      path: project.path,
      status_source: project.status_source,
      display_priority: project.display_priority || "medium"
    }));
  }
  function priorityScore(value) {
    switch (value) {
      case "high":
        return 0;
      case "medium":
        return 1;
      case "low":
        return 2;
      default:
        return 9;
    }
  }
  function sortProjects(projects) {
    return [...projects].sort((a, b) => {
      const p = priorityScore(a.display_priority) - priorityScore(b.display_priority);
      if (p !== 0) return p;
      return String(a.id).localeCompare(String(b.id), "ja");
    });
  }
  function buildFallbackState(project) {
    return {
      project_id: project.id,
      current_phase: "未設定",
      current_session_id: "未設定",
      status: "idle",
      waiting_for: null,
      last_updated: null,
      last_error: null,
      summary: "データ未整備",
      next_action: "state.json を配置してください",
      __fallback: true
    };
  }
  function normalizeState(project, rawState) {
    if (!rawState || typeof rawState !== "object") {
      return buildFallbackState(project);
    }
    return {
      project_id: rawState.project_id || project.id,
      current_phase: rawState.current_phase || "未設定",
      current_session_id: rawState.current_session_id || "未設定",
      status: rawState.status || "idle",
      waiting_for: rawState.waiting_for ?? null,
      last_updated: rawState.last_updated || null,
      last_error: rawState.last_error ?? null,
      summary: rawState.summary || "要約未設定",
      next_action: rawState.next_action || "次アクション未設定",
      __fallback: false
    };
  }
  function renderQueue(queueState) {
    const box = document.getElementById("queue-box");
    if (!queueState || !Array.isArray(queueState.jobs)) {
      box.innerHTML = `
        <div>queue_state.json 未整備</div>
        <div class="small muted">viewer は queue 情報がなくても継続描画します。</div>
      `;
      return;
    }
    const counts = {
      PENDING: 0,
      RUNNING: 0,
      COMPLETED: 0,
      FAILED: 0,
      DEAD_LETTER: 0
    };
    for (const job of queueState.jobs) {
      if (Object.prototype.hasOwnProperty.call(counts, job.status)) {
        counts[job.status] += 1;
      }
    }
    box.innerHTML = `
      <div>queue_version: <strong>${escapeHtml(queueState.queue_version || "unknown")}</strong></div>
      <div>last_updated: <strong>${escapeHtml(queueState.last_updated || "unknown")}</strong></div>
      <div class="small" style="margin-top: 8px;">
        PENDING: ${counts.PENDING} /
        RUNNING: ${counts.RUNNING} /
        COMPLETED: ${counts.COMPLETED} /
        FAILED: ${counts.FAILED} /
        DEAD_LETTER: ${counts.DEAD_LETTER}
      </div>
    `;
  }
  function renderSummary(states) {
    const total = states.length;
    const waiting = states.filter((s) => s.status === "waiting").length;
    const running = states.filter((s) => s.status === "running").length;
    const risk = states.filter((s) => s.status === "blocked" || s.status === "error").length;
    document.getElementById("summary-total").textContent = String(total);
    document.getElementById("summary-waiting").textContent = String(waiting);
    document.getElementById("summary-running").textContent = String(running);
    document.getElementById("summary-risk").textContent = String(risk);
  }
  function renderProjects(projectsWithState) {
    const list = document.getElementById("project-list");
    list.innerHTML = "";
    for (const item of projectsWithState) {
      const project = item.project;
      const state = item.state;
      const statusMeta = STATUS_META[state.status] || STATUS_META.idle;
      const waitingFor = state.waiting_for ? state.waiting_for : "—";
      const lastUpdated = state.last_updated ? state.last_updated : "未更新";
      const lastError = state.last_error ? state.last_error : null;
      const card = document.createElement("article");
      card.className = "project-card";
      card.innerHTML = `
        <div class="project-top">
          <div class="project-title-wrap">
            <div class="project-id">${escapeHtml(project.id)}</div>
            <div class="project-name">${escapeHtml(project.name)}</div>
          </div>
          <div class="badge ${statusMeta.className}">
            <span>${statusMeta.icon}</span>
            <span>${escapeHtml(statusMeta.label)}</span>
          </div>
        </div>
        <div class="project-grid">
          <div class="field">
            <span class="field-label">Phase</span>
            <div class="field-value">${escapeHtml(state.current_phase)}</div>
          </div>
          <div class="field">
            <span class="field-label">Session</span>
            <div class="field-value">${escapeHtml(state.current_session_id)}</div>
          </div>
          <div class="field">
            <span class="field-label">Waiting for</span>
            <div class="field-value">${escapeHtml(waitingFor)}</div>
          </div>
          <div class="field">
            <span class="field-label">Last updated</span>
            <div class="field-value">${escapeHtml(lastUpdated)}</div>
          </div>
        </div>
        <div class="field" style="margin-bottom: 10px;">
          <span class="field-label">Summary</span>
          <div class="field-value">${escapeHtml(state.summary || "—")}</div>
        </div>
        <div class="field">
          <span class="field-label">Next action</span>
          <div class="field-value">${escapeHtml(state.next_action || "—")}</div>
        </div>
        ${lastError ? `
          <div class="error-box">
            <span class="field-label">Latest error</span>
            <div class="field-value">${escapeHtml(lastError)}</div>
          </div>
        ` : ""}
      `;
      list.appendChild(card);
    }
  }
  async function loadProjectsRegistry() {
    const yamlText = await fetchText(PATHS.projectsYaml);
    const parsed = window.jsyaml.load(yamlText);
    return normalizeProjectsYaml(parsed);
  }
  async function loadProjectState(project) {
    const state = await tryFetchJson(`../${project.status_source}`);
    return normalizeState(project, state);
  }
  async function init() {
    try {
      setGlobalMessage("読込中...", "loading");
      const projects = sortProjects(await loadProjectsRegistry());
      const queueState = await tryFetchJson(PATHS.queueState);
      const projectsWithState = [];
      for (const project of projects) {
        const state = await loadProjectState(project);
        projectsWithState.push({ project, state });
      }
      renderQueue(queueState);
      renderSummary(projectsWithState.map((x) => x.state));
      renderProjects(projectsWithState);
      setGlobalMessage("", "");
      updateLastUpdated(new Date().toLocaleString("ja-JP"));
    } catch (error) {
      console.error(error);
      setGlobalMessage(
        `初期化に失敗しました: ${error.message}。` +
        ` python3 -m http.server 8080 で起動しているか確認してください。`,
        "error"
      );
      updateLastUpdated("失敗");
    }
  }
  document.addEventListener("DOMContentLoaded", init);
})();
