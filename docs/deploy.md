# 배포 가이드 — 이 Mac + Tailscale Funnel (2026-11-19)

sudo-quest 때와 같은 방식이다: **서버는 이 Mac에서 돌리고, Tailscale Funnel이 그 포트 하나만 인터넷에 연결**한다.
이 프로젝트는 FastAPI가 화면(`frontend/dist`)과 API를 **한 주소**로 내보내므로 GitHub Pages·CORS 설정이 필요 없다.

```
방문자 ──https──> https://<이 Mac 이름>.<tailnet>.ts.net   (Tailscale Funnel, 443)
                         │
                         └──> http://127.0.0.1:8010   scripts/serve.sh --public  (공개 모드, data/public.db)
```

## 한눈에

| 하는 일 | 명령 |
|---|---|
| 공개 모드 서버 켜기 | `scripts/serve.sh --public` (화면 빌드 → 127.0.0.1:8010) |
| 밖으로 열기 | `tailscale funnel --bg 8010` |
| 지금 상태 | `tailscale funnel status` · `curl -s https://<주소>/health` → `{"ok":true,"public":true}` |
| 밖으로 닫기 (바로 차단) | `tailscale funnel reset` |
| 서버 끄기 | 서버 창에서 Ctrl+C |

- Funnel 켜기·끄기는 **사용자가 직접** 한다 (밖으로 공개하는 일이라).
- `tailscale funnel --bg 8010`은 Mac을 다시 켜도 유지된다. 서버가 꺼져 있으면 방문자에게는 연결 오류가 보인다.
- sudo-quest도 같이 열어야 하면 공개 포트를 나눈다: 예) sudo-patch는 `tailscale funnel --bg --https=8443 8010` → `https://<주소>:8443`.

## 공개 모드가 하는 일 (spec v1.24)

로컬(`scripts/serve.sh`, 기본)은 지금까지와 같다. `--public`일 때만:

| 막는 것 | 방법 |
|---|---|
| 남의 계획·로그·일정 보기·지우기 | 화면이 모든 요청에 세션 아이디(무작위 32자)를 `X-Session-Id`로 보내고, 서버는 그 세션 것만 돌려준다. 남의 것은 404. 캘린더 일정에는 주인(owner) 칸 |
| 누구나 LLM(GMS) 비용 쓰기 | `/chat` IP당 시간당 20회, 서버 전체 하루 300회 · `/upload` IP당 시간당 60회 → 넘으면 429 "허허, 진료 대기가 길어졌네요. 잠시 뒤에 다시 오시죠." |
| 로컬 테스트 데이터와 섞임 | `DB_PATH=data/public.db` (git에 안 올라감, `*.db`) |

- 상한 값은 `.env`나 환경 변수로: `PUBLIC_CHAT_PER_HOUR`, `PUBLIC_CHAT_PER_DAY`, `PUBLIC_UPLOAD_PER_HOUR` (0이면 상한 없음). 서버를 다시 켜면 횟수는 처음부터.
- 업로드 1MB, 메시지 2000자 제한은 원래 있음.
- 화면의 "모든 계획 보기" 토글은 공개 모드에서 숨는다.

## 처음 한 번 (이미 sudo-quest 때 했으면 건너뜀)

1. Tailscale 앱 설치·로그인 (`brew install --cask tailscale-app`, Mac 비밀번호는 사용자가 입력).
2. `tailscale funnel --bg 8010` 처음 실행 때 브라우저에서 Funnel 허용.
3. `.env`에 `GMS_KEY`·`GMS_BASE_URL`·`LLM_MODEL` (키는 `.env`에만, 커밋 안 함).

## 공개 후 확인할 것

- [ ] 밖(휴대폰 LTE 등)에서 `https://<주소>` → 진료실이 뜨고 예시 하나가 끝까지 돈다.
- [ ] 다른 기기에서 연 화면에 내 계획·일정·로그가 보이지 않는다.
- [ ] **IP 구분:** Funnel이 `X-Forwarded-For`를 붙이는지 서버 로그로 확인. 안 붙이면 모든 방문자가 같은 IP(127.0.0.1)로 보여 IP 상한이 사실상 전체 상한(시간당 20회)이 된다 — 더 엄격한 쪽이라 안전하지만, 시연 중 막히면 `PUBLIC_CHAT_PER_HOUR`를 올린다.
- [ ] 끝나면 `tailscale funnel reset`.

## 문제 생길 때

| 증상 | 확인 |
|---|---|
| 밖에서 안 열림 | 서버가 떠 있는지 `curl -s 127.0.0.1:8010/health`, `tailscale funnel status` |
| "설정 필요" (API 키) | `.env`의 GMS 값, 서버 다시 켜기 |
| "진료 대기가 길어졌네요" | 상한에 걸림. 시간이 지나거나 서버를 다시 켜면 풀림 |
| 화면이 옛 모습 | `scripts/serve.sh --public`이 빌드까지 하므로 다시 실행 |
