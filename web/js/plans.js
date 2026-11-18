// ② 계획 관리 탭: 날짜순 목록, 겹침 경고, 날짜·시각 수정, 삭제 (F3015·F3016)
const Plans = (() => {
  const $ = (id) => document.getElementById(id);

  function card(p) {
    return `
      <div class="card plan-card" data-id="${p.id}">
        <div class="round-head">
          <div>
            <strong>${p.round_no ? `${p.round_no}회차 · ` : ""}${R.esc(p.date)}</strong>
            <span class="extra">${R.timeWindow(p.window_start, p.window_end)}</span>
            ${R.overlapBadge(p.overlaps)}
          </div>
          <div class="actions">
            <button class="btn small" data-act="edit" type="button">수정</button>
            <button class="btn small danger" data-act="delete" type="button">삭제</button>
          </div>
        </div>
        <div class="edit-row" hidden>
          <label>날짜 <input type="date" name="date" value="${R.esc(p.date)}"></label>
          <label>시작 <input type="time" name="window_start" value="${R.esc(p.window_start || "")}"></label>
          <label>종료 <input type="time" name="window_end" value="${R.esc(p.window_end === "24:00" ? "23:59" : p.window_end || "")}"></label>
          <button class="btn small primary" data-act="save" type="button">저장</button>
          <button class="btn small ghost" data-act="cancel" type="button">취소</button>
        </div>
        <table class="items">${R.itemRows(p.items)}</table>
        <div class="meta">만든 때 ${R.esc(p.created_at.replace("T", " ").slice(0, 16))}${p.updated_at !== p.created_at ? ` · 고친 때 ${R.esc(p.updated_at.replace("T", " ").slice(0, 16))}` : ""}</div>
      </div>`;
  }

  async function load() {
    try {
      const plans = await Api.listPlans();
      $("plans").innerHTML = plans.length ? plans.map(card).join("")
        : '<div class="empty">저장한 계획이 없어요. 대화 탭에서 계획을 만든 뒤 "이 계획 확정"을 눌러 주세요.</div>';
    } catch (err) {
      App.notice(err.message, "error");
    }
  }

  async function onClick(e) {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const cardEl = btn.closest(".plan-card");
    const id = cardEl.dataset.id;
    const edit = cardEl.querySelector(".edit-row");
    try {
      if (btn.dataset.act === "edit") edit.hidden = false;
      if (btn.dataset.act === "cancel") edit.hidden = true;
      if (btn.dataset.act === "save") {
        // 바꾼 칸만 보낸다 (시각 입력칸은 24:00을 23:59로 보여 주므로, 안 바꿨으면 원래 값 유지)
        const changes = {};
        edit.querySelectorAll("input").forEach((input) => {
          if (input.value !== input.defaultValue) changes[input.name] = input.value || null;
        });
        if (!Object.keys(changes).length) { edit.hidden = true; return; }
        const updated = await Api.updatePlan(id, changes);
        App.notice(updated.overlaps.length ? `저장했어요. 같은 날 시간이 겹치는 계획이 ${updated.overlaps.length}개 있어요.` : null);
        await load();
      }
      if (btn.dataset.act === "delete") {
        if (!confirm("이 계획을 삭제할까요? 되돌릴 수 없어요.")) return;
        await Api.deletePlan(id);
        await load();
      }
    } catch (err) {
      App.notice(err.message, "error");
    }
  }

  function init() {
    $("plans").addEventListener("click", onClick);
    $("plans-refresh").addEventListener("click", load);
  }

  return { init, load };
})();
