// 백엔드 API 호출 (spec "백엔드 API"). 화면에는 서버가 준 짧은 안내만 보여준다.
const Api = (() => {
  const SESSION_KEY = "sudo-patch.session";

  function getSession() {
    try { return localStorage.getItem(SESSION_KEY); } catch { return null; }
  }
  function setSession(id) {
    try { id ? localStorage.setItem(SESSION_KEY, id) : localStorage.removeItem(SESSION_KEY); } catch { /* 저장 못 해도 동작 */ }
  }

  async function json(method, url, body) {
    let res;
    try {
      res = await fetch(url, {
        method,
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new Error("서버에 연결하지 못했어요. 서버가 켜져 있는지 확인해 주세요.");
    }
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "요청을 처리하지 못했어요.");
    return data;
  }

  async function upload(file) {
    const session = getSession();
    const url = "/upload" + (session ? `?session_id=${encodeURIComponent(session)}` : "");
    let res;
    try {
      res = await fetch(url, { method: "POST", body: file });
    } catch {
      throw new Error("서버에 연결하지 못했어요.");
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "파일을 올리지 못했어요.");
    setSession(data.session_id);
    return data;
  }

  // POST /chat 의 ndjson 스트림을 한 줄씩 onEvent로 넘긴다. 마지막 final 이벤트를 돌려준다.
  async function chat(message, onEvent) {
    let res;
    try {
      res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: getSession(), message }),
      });
    } catch {
      throw new Error("서버에 연결하지 못했어요.");
    }
    if (!res.ok || !res.body) {
      const data = await res.json().catch(() => ({}));
      throw new Error(typeof data.detail === "string" ? data.detail : "메시지를 보내지 못했어요.");
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let final = null;
    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let nl;
        while ((nl = buffer.indexOf("\n")) >= 0) {
          const line = buffer.slice(0, nl).trim();
          buffer = buffer.slice(nl + 1);
          if (!line) continue;
          const event = JSON.parse(line);
          if (event.type === "session") setSession(event.session_id);
          if (event.type === "final") final = event;
          onEvent(event);
        }
      }
    } catch {
      throw new Error("연결이 끊겼어요. 잠시 후 다시 시도해 주세요.");
    }
    if (!final) throw new Error("연결이 끊겼어요. 답을 끝까지 받지 못했어요.");
    return final;
  }

  return {
    getSession, setSession, upload, chat,
    listPlans: () => json("GET", "/plans"),
    updatePlan: (id, changes) => json("PUT", `/plans/${id}`, changes),
    deletePlan: (id) => json("DELETE", `/plans/${id}`),
    listLogs: () => json("GET", "/logs"),
    getLog: (sid) => json("GET", `/logs/${encodeURIComponent(sid)}`),
    deleteLog: (sid) => json("DELETE", `/logs/${encodeURIComponent(sid)}`),
  };
})();
