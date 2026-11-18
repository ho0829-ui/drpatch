// 화면 그리기 도우미. 서버·LLM이 준 글자는 모두 escape한 뒤에만 넣는다 (스크립트 삽입 방지).
const R = (() => {
  function esc(text) {
    return String(text ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // LLM 답의 간단한 서식만: **굵게**, `코드`, "- " 목록, 줄바꿈
  function markdown(text) {
    const lines = esc(text).split("\n");
    let html = "";
    let inList = false;
    for (const raw of lines) {
      let line = raw.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
      const item = line.match(/^\s*[-*]\s+(.*)$/);
      if (item) {
        if (!inList) { html += "<ul>"; inList = true; }
        html += `<li>${item[1]}</li>`;
        continue;
      }
      if (inList) { html += "</ul>"; inList = false; }
      html += line.trim() ? `<p>${line}</p>` : "";
    }
    return html + (inList ? "</ul>" : "");
  }

  const SEVERITY = { CRITICAL: "CRITICAL", HIGH: "HIGH", MODERATE: "MODERATE", LOW: "LOW", UNKNOWN: "심각도 미상" };
  const KIND = { python_upgrade: "Python", os: "OS", package: "" };

  function severity(s) {
    return s ? `<span class="badge ${esc(s)}">${esc(SEVERITY[s] || s)}</span>` : "";
  }

  function itemRows(items) {
    return items.map((i) => {
      const target = i.target_version ? ` → <strong>${esc(i.target_version)}</strong>` : " → <em>올림 필요</em>";
      const flags = (i.flags || []).map((f) => `<span class="badge flag">${esc(f)}</span>`).join("");
      const kind = KIND[i.kind] && KIND[i.kind] !== i.name ? `<span class="badge">${KIND[i.kind]}</span>` : "";
      return `<tr>
        <td>${kind}<strong>${esc(i.name)}</strong></td>
        <td class="ver">${esc(i.current_version)}${target}</td>
        <td>${severity(i.severity)}${flags}<div class="reason">${esc(i.reason)}</div></td>
      </tr>`;
    }).join("");
  }

  function timeWindow(start, end) {
    if (!start && !end) return "하루 전체";
    return `${esc(start || "00:00")}~${esc(end || "24:00")}`;
  }

  function overlapBadge(overlaps) {
    if (!overlaps || !overlaps.length) return "";
    const list = overlaps.map((o) => `${o.date} ${timeWindow(o.window_start, o.window_end)}`).join(", ");
    return `<span class="badge overlap" title="${esc(list)}">⚠ 시간이 겹치는 계획 ${overlaps.length}개</span>`;
  }

  // final.plan → 회차 카드들 + 안전·확인 못 함·보류·미배정
  function planView(plan) {
    if (!plan) return "";
    const window = plan.window || {};
    const rounds = plan.rounds.map((r) => `
      <div class="round">
        <div class="round-head"><strong>${r.round_no}회차 · ${esc(r.date)}</strong>
          <span class="extra">${timeWindow(window.start, window.end)}
            ${r.moved_from ? `<span class="badge flag">일정 충돌로 이동 (원래 ${esc(r.moved_from)})</span>` : ""}
            ${(r.calendar_conflicts || []).length ? `<span class="badge overlap">⚠ 일정과 겹침: ${esc(r.calendar_conflicts.join(", "))}</span>` : ""}
          </span></div>
        <table class="items">${itemRows(r.items)}</table>
      </div>`).join("");
    const extras = [
      ["미배정", plan.unassigned.map((i) => i.name)],
      ["안전(취약점 0건)", plan.safe],
      ["확인 못 함", plan.unchecked.map((u) => `${u.name} (${u.reason})`)],
      ["보류", plan.held.map((h) => `${h.name} (${h.reason})`)],
      ["조회 제외", (plan.excluded || []).map((e) => `${e.line_no}번 줄 (${e.reason})`)],
    ].filter(([, names]) => names.length)
      .map(([label, names]) => `<div class="extra"><b>${label}</b>: ${names.map(esc).join(", ")}</div>`).join("");
    const priority = !rounds && plan.priority && plan.priority.length ? `
      <div class="round">
        <div class="round-head"><strong>위험한 순서</strong><span class="extra">일정을 알려 주면 회차로 나눠요</span></div>
        <table class="items">${itemRows(plan.priority)}</table>
      </div>` : "";
    const body = rounds || priority || '<div class="extra">이번에 계획에 넣을 항목이 없어요.</div>';
    return `<div class="plan-view">${body}${extras}</div>`;
  }

  // 실행 이벤트 한 줄 (대화 탭 실행 단계 패널, 로그 탭이 같이 씀)
  const STEP = { analyze: "요청 분석", ask: "빠진 입력 묻기", plan_tools: "Tool 계획", call_tools: "Tool 호출",
                 judge: "판단", replan: "재계획", build: "회차 나누기", respond: "응답 작성", fact: "사실 조회", other: "대화" };
  const DECISION = { intent: "의도", tool_plan: "Tool 순서", replan_strategy: "재계획 방식" };

  function eventItem(e, time) {
    const t = time ? `<span class="t">${esc(time)}</span>` : "";
    switch (e.type) {
      case "step_start":
        return `<li class="step">${esc(STEP[e.step] || e.step)}${t}</li>`;
      case "step_end":
        return "";
      case "tool_call":
        return "";
      case "tool_result": {
        const target = Object.values(e.args || {}).join(" ");
        const mark = e.ok ? "✓" : `✗ ${esc(e.error_code)} → 확인 못 함`;
        return `<li class="tool ${e.ok ? "" : "fail"}">${esc(e.tool)}(${esc(target)}) ${mark} <span class="t">${esc(e.ms)}ms</span></li>`;
      }
      case "llm_decision": {
        let what = e.intent || (e.steps && e.steps.join(" → ")) || e.strategy || "";
        return `<li class="decision">LLM 판단 · ${esc(DECISION[e.decision] || e.decision)}: <b>${esc(what)}</b>${t}
          <span class="why">${esc(e.reason || "")}</span></li>`;
      }
      case "judgment": {
        const v = e.violations || [];
        return `<li>판단: ${v.length ? `지금 Python으로는 안전한 버전이 없음 → ${esc(v.join(", "))}` : "모두 지금 Python에서 해결 가능"}</li>`;
      }
      case "replan":
        if (e.result === "hold") return `<li class="replan">재계획 중단 → 보류<span class="why">${esc(e.reason)}</span></li>`;
        return `<li class="replan">재계획 ${esc(e.no)}회 · Python ${esc(e.python)}${t}<span class="why">${esc(e.reason)}</span></li>`;
      case "plan_built":
        return `<li class="plan">회차 배정: ${e.rounds.map((r) => `${r.round_no}회차 [${esc(r.items.join(", "))}]`).join(" · ")}
          <span class="why">${esc(e.rule)}</span></li>`;
      case "calendar_check": {
        const moved = (e.rounds || []).filter((r) => r.moved_from);
        const text = e.status !== "확인함" ? `캘린더 ${esc(e.status)}`
          : moved.length ? moved.map((r) => `${r.round_no}회차 ${esc(r.moved_from)} → ${esc(r.date)}`).join(", ") + " (일정 충돌로 이동)"
          : "캘린더: 겹치는 일정 없음";
        return `<li class="${moved.length ? "replan" : "plan"}">${text}${t}</li>`;
      }
      case "error":
        return `<li class="error">문제 발생 (${esc(STEP[e.step] || e.step)})</li>`;
      default:
        return "";
    }
  }

  return { esc, markdown, planView, itemRows, timeWindow, overlapBadge, eventItem, severity };
})();
