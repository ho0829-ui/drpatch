// ① 대화 탭: 파일 올리기, 채팅, 실행 단계 패널 (F3018·F3019)
const Chat = (() => {
  const $ = (id) => document.getElementById(id);
  let busy = false;
  let startedAt = 0;

  function addMessage(role, html) {
    const box = document.createElement("div");
    box.className = `msg ${role}`;
    box.innerHTML = `<div class="bubble">${html}</div>`;
    $("messages").appendChild(box);
    $("messages").scrollTop = $("messages").scrollHeight;
    return box.querySelector(".bubble");
  }

  function setStatus(kind, text) {
    const el = $("steps-status");
    el.className = `status ${kind}`;
    el.textContent = text;
  }

  function addStep(event) {
    const elapsed = ((performance.now() - startedAt) / 1000).toFixed(1) + "s";
    const html = R.eventItem(event, elapsed);
    if (!html) return;
    $("steps").insertAdjacentHTML("beforeend", html);
    $("steps").scrollTop = $("steps").scrollHeight;
  }

  function showUpload(data) {
    const ex = data.excluded;
    $("upload-result").hidden = false;
    $("upload-result").innerHTML = `
      ✓ 조회할 패키지 <b>${data.packages.length}개</b>${ex.length ? `, 조회 제외 <b>${ex.length}개</b>` : ""}
      ${ex.length ? `<ul>${ex.map((e) => `<li>${e.line_no}번 줄 <code>${R.esc(e.text)}</code> — ${R.esc(e.reason)}</li>`).join("")}</ul>` : ""}`;
  }

  async function onFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const data = await Api.upload(file);
      showUpload(data);
      addMessage("bot", `파일을 받았어요. 패키지 ${data.packages.length}개를 조회할게요. 이제 OS·Python 버전과 일정을 알려 주세요.`);
    } catch (err) {
      App.notice(err.message, "error");
    } finally {
      e.target.value = "";
    }
  }

  function confirmButton(bubble) {
    const btn = document.createElement("button");
    btn.className = "btn primary small";
    btn.type = "button";
    btn.textContent = "이 계획 확정";
    btn.style.marginTop = "10px";
    btn.addEventListener("click", () => { btn.disabled = true; send("확정해줘"); });
    bubble.appendChild(btn);
  }

  function showFinal(bubble, final) {
    bubble.innerHTML = R.markdown(final.answer || "");
    if (final.plan) {
      bubble.insertAdjacentHTML("beforeend", R.planView(final.plan));
      if (final.plan.rounds.length) confirmButton(bubble);
    }
    if (final.confirmed) {
      const overlapped = final.confirmed.filter((p) => p.overlaps.length);
      bubble.insertAdjacentHTML("beforeend", `<div class="extra" style="margin-top:8px">
        <b>저장했어요</b>: ${final.confirmed.map((p) => `${p.round_no}회차 ${R.esc(p.date)}`).join(", ")} — 계획 관리 탭에서 볼 수 있어요.
        ${overlapped.length ? `<br>${R.overlapBadge(overlapped.flatMap((p) => p.overlaps))}` : ""}</div>`);
      Plans.load();
    }
    if (final.intent === "error") App.notice(final.answer, "error");
  }

  async function send(message) {
    if (busy || !message.trim()) return;
    busy = true;
    $("send").disabled = true;
    App.notice(null);
    addMessage("user", R.esc(message));
    const bubble = addMessage("bot", '<span class="thinking">처리 중…</span>');
    $("steps").innerHTML = "";
    startedAt = performance.now();
    setStatus("running", "처리 중");
    try {
      const final = await Api.chat(message, (event) => {
        if (event.type !== "final" && event.type !== "session") addStep(event);
      });
      showFinal(bubble, final);
      setStatus(final.intent === "error" ? "error" : "done",
        `완료 ${((performance.now() - startedAt) / 1000).toFixed(1)}초`);
    } catch (err) {
      bubble.innerHTML = R.esc(err.message);
      setStatus("error", "중단");
      App.notice(err.message, "error");
    } finally {
      busy = false;
      $("send").disabled = false;
      $("messages").scrollTop = $("messages").scrollHeight;
    }
  }

  function init() {
    $("file").addEventListener("change", onFile);
    $("chat-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const input = $("chat-input");
      const text = input.value;
      input.value = "";
      send(text);
    });
    $("new-session").addEventListener("click", () => {
      if (busy) return;
      Api.setSession(null);
      $("messages").innerHTML = "";
      $("steps").innerHTML = "";
      $("upload-result").hidden = true;
      setStatus("idle", "대기");
      addMessage("bot", "새 대화를 시작했어요. requirements.txt부터 올려 주세요.");
    });
  }

  return { init, send };
})();
