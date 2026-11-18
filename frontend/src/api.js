const SESSION_KEY = 'sudo-patch.session';
const MAX_UPLOAD_BYTES = 1024 * 1024; // 1MB

export function getSession() {
  try {
    return localStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
}

export function setSession(id) {
  try {
    if (id) localStorage.setItem(SESSION_KEY, id);
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    /* 저장 못 해도 동작 */
  }
}

async function requestJson(method, url, body) {
  let res;
  try {
    res = await fetch(url, {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error('서버에 연결하지 못했어요. 서버가 켜져 있는지 확인해 주세요.');
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : '요청을 처리하지 못했어요.');
  }
  return data;
}

/** POST /upload (본문 = 파일 그대로, 1MB 제한) → { session_id, packages, excluded, saved } */
export async function upload(file, sessionId = getSession()) {
  if (file && typeof file.size === 'number' && file.size > MAX_UPLOAD_BYTES) {
    throw new Error('파일 크기는 1MB 이하여야 해요.');
  }
  const url = '/upload' + (sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '');
  let res;
  try {
    res = await fetch(url, { method: 'POST', body: file });
  } catch {
    throw new Error('서버에 연결하지 못했어요.');
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : '파일을 올리지 못했어요.');
  }
  setSession(data.session_id);
  return data;
}

/**
 * POST /chat ndjson 스트림을 줄 단위로 읽어 onEvent(event) 호출, 마지막 final 객체 반환.
 * 줄 종류: {type:"session"} → 실행 이벤트들({type, seq, ...}) → {type:"final", ...}
 */
export async function chat(sessionId, message, onEvent) {
  const sid = sessionId ?? getSession();
  let res;
  try {
    res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sid, message }),
    });
  } catch {
    throw new Error('서버에 연결하지 못했어요.');
  }
  if (!res.ok || !res.body) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : '메시지를 보내지 못했어요.');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let final = null;

  const handleLine = (raw) => {
    const line = raw.trim();
    if (!line) return;
    const event = JSON.parse(line);
    if (event.type === 'session') setSession(event.session_id);
    if (event.type === 'final') final = event;
    onEvent?.(event);
  };

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let nl;
      while ((nl = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, nl);
        buffer = buffer.slice(nl + 1);
        handleLine(line);
      }
    }
    buffer += decoder.decode();
    if (buffer.trim()) handleLine(buffer);
  } catch {
    throw new Error('연결이 끊겼어요. 잠시 후 다시 시도해 주세요.');
  }

  if (!final) {
    throw new Error('연결이 끊겼어요. 답을 끝까지 받지 못했어요.');
  }
  return final;
}

export const plans = {
  list: (sessionId) =>
    requestJson('GET', sessionId ? `/plans?session_id=${encodeURIComponent(sessionId)}` : '/plans'),
  get: (id) => requestJson('GET', `/plans/${id}`),
  update: (id, changes) => requestJson('PUT', `/plans/${id}`, changes),
  remove: (id) => requestJson('DELETE', `/plans/${id}`),
};

export const logs = {
  list: () => requestJson('GET', '/logs'),
  get: (sessionId) => requestJson('GET', `/logs/${encodeURIComponent(sessionId)}`),
  remove: (sessionId) => requestJson('DELETE', `/logs/${encodeURIComponent(sessionId)}`),
};

export const calendar = {
  list: (dateFrom, dateTo) => {
    const params = new URLSearchParams();
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    const qs = params.toString();
    return requestJson('GET', qs ? `/calendar/events?${qs}` : '/calendar/events');
  },
  add: ({ title, date, start, end }) =>
    requestJson('POST', '/calendar/events', { title, date, start, end }),
  remove: (id) => requestJson('DELETE', `/calendar/events/${id}`),
};
