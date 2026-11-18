// ③ 실행 로그 탭: 세션 목록 → 이벤트 순서대로, 삭제 (F3014). 수정 기능은 없다.
const Logs = (() => {
  const $ = (id) => document.getElementById(id);
  let current = null;

  function when(iso) {
    return R.esc((iso || "").replace("T", " ").slice(0, 19));
  }

  async function load() {
    try {
      const sessions = await Api.listLogs();
      $("log-sessions").innerHTML = sessions.length ? sessions.map((s) => `
        <li><button type="button" data-sid="${R.esc(s.session_id)}" class="${s.session_id === current ? "active" : ""}">
          <span class="mono">${R.esc(s.session_id.slice(0, 12))}</span>
          <span class="meta">이벤트 ${s.events}개 · ${when(s.last_at)}</span>
        </button></li>`).join("") : '<li class="empty">아직 실행 로그가 없어요.</li>';
    } catch (err) {
      App.notice(err.message, "error");
    }
  }

  // 로그 한 줄: 화면용 표시를 쓰고, 단계 끝은 요약만, Tool 호출 요청은 결과 줄이 있으니 생략
  function logLine(e) {
    if (e.type === "tool_call") return "";
    if (e.type === "step_end") {
      const { step, ...summary } = e.payload;
      const parts = Object.entries(summary).filter(([, v]) => v !== null && v !== undefined && !(Array.isArray(v) && !v.length))
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`);
      return parts.length ? `<li class="tool"><span class="t">#${e.seq}</span> └ ${R.esc(parts.join(" · "))}</li>` : "";
    }
    const line = R.eventItem({ ...e.payload, type: e.type }, `#${e.seq}`);
    return line || `<li><span class="t">#${e.seq}</span> ${R.esc(e.type)}<span class="payload">${R.esc(JSON.stringify(e.payload))}</span></li>`;
  }

  async function show(sid) {
    current = sid;
    try {
      const { events } = await Api.getLog(sid);
      $("log-title").textContent = `세션 ${sid.slice(0, 12)} · 이벤트 ${events.length}개`;
      $("log-delete").hidden = false;
      $("log-events").innerHTML = events.map(logLine).join("");
      load();
    } catch (err) {
      App.notice(err.message, "error");
    }
  }

  async function remove() {
    if (!current || !confirm("이 세션의 실행 로그를 삭제할까요? 되돌릴 수 없어요.")) return;
    try {
      await Api.deleteLog(current);
      current = null;
      $("log-title").textContent = "세션을 고르세요";
      $("log-delete").hidden = true;
      $("log-events").innerHTML = "";
      load();
    } catch (err) {
      App.notice(err.message, "error");
    }
  }

  function init() {
    $("log-sessions").addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-sid]");
      if (btn) show(btn.dataset.sid);
    });
    $("logs-refresh").addEventListener("click", load);
    $("log-delete").addEventListener("click", remove);
  }

  return { init, load };
})();
