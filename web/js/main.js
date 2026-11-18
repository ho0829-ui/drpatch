// 탭 전환과 상단 안내 띠
const App = (() => {
  function notice(message, kind = "warn") {
    const el = document.getElementById("notice");
    if (!message) { el.hidden = true; return; }
    el.className = `notice ${kind === "error" ? "error" : ""}`;
    el.textContent = message;
    el.hidden = false;
  }

  function showTab(name) {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${name}`));
    if (name === "plans") Plans.load();
    if (name === "logs") Logs.load();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => showTab(t.dataset.tab)));
    Chat.init();
    Plans.init();
    Logs.init();
  });

  return { notice, showTab };
})();
