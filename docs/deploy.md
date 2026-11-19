# 배포 가이드 — GitHub Pages(화면) + 이 Mac·Tailscale Funnel(API) (2026-11-19)

sudo-quest 때와 같은 방식이다.

```
방문자 ─https─> https://ho0829-ui.github.io/sudo-patch/      화면 (GitHub Pages: 3D 모델 17MB·JS·CSS)
                    │  API 호출만 (작은 JSON·대화 스트림)
                    └─https─> https://macmini.taile20f54.ts.net   Tailscale Funnel (443)
                                   └─> http://127.0.0.1:8010       scripts/serve.sh --public (공개 모드, data/public.db)
```

- **왜 나눴나:** 무거운 화면 파일을 Mac에서 Funnel로 내보내면 밖에서 아주 느리다(2026-11-19 사용자 확인). Pages(GitHub CDN)가 화면을, Mac은 가벼운 API만 맡는다.
- Funnel 주소로 직접 들어가도 화면이 뜬다(서버가 `frontend/dist`도 내보냄) — 비상용. 평소 주소는 Pages.

## 한눈에

| 하는 일 | 명령 / 위치 |
|---|---|
| 공개 모드 API 서버 켜기 | `scripts/serve.sh --public` (127.0.0.1:8010) |
| 밖으로 열기 / 닫기 | `tailscale funnel --bg 8010` / `tailscale funnel reset` |
| 상태 | `tailscale funnel status` · `curl -s https://macmini.taile20f54.ts.net/health` → `{"ok":true,"public":true}` |
| 화면 배포 | `main`에 push → GitHub Actions `pages` (테스트 → 빌드 → Pages) |
| 화면 주소 | https://ho0829-ui.github.io/sudo-patch/ |

## 처음 한 번 (사용자)

1. **GitHub Pages 켜기:** 저장소 Settings → Pages → Source를 **GitHub Actions**로.
2. **API 주소 변수:** Settings → Secrets and variables → Actions → **Variables** → `API_BASE_URL` = `https://macmini.taile20f54.ts.net`
   (공개 주소일 뿐 비밀이 아니다. `GMS_KEY`는 절대 GitHub에 넣지 않는다 — Mac의 `.env`에만.)
3. `main`에 push → Actions 탭에서 `pages`가 초록색이면 위 화면 주소로 들어간다.
4. Tailscale: 로그인돼 있고 Funnel 허용됨 (sudo-quest 때 함). `tailscale funnel --bg 8010`.

## 공개 모드가 하는 일 (spec v1.24·v1.25)

로컬(`scripts/serve.sh`, 기본)은 지금까지와 같다. `--public`일 때만:

| 막는 것 | 방법 |
|---|---|
| 남의 계획·로그·일정 보기·지우기 | 화면이 모든 요청에 세션 아이디(무작위 32자)를 `X-Session-Id`로 보내고, 서버는 그 세션 것만. 남의 것은 404. 캘린더 일정에 주인(owner) 칸 |
| 누구나 LLM(GMS) 비용 쓰기 | `/chat` IP당 시간당 20회·전체 하루 300회, `/upload` IP당 시간당 60회 → 429 "허허, 진료 대기가 길어졌네요. 잠시 뒤에 다시 오시죠." |
| 다른 사이트가 API를 부르기 | CORS는 `ALLOWED_ORIGINS`(기본 `https://ho0829-ui.github.io`)만. Chrome 사설망 확인(Private Network Access)도 그 주소에만 허용 |
| 로컬 테스트 데이터와 섞임 | `DB_PATH=data/public.db` (git에 안 올라감) |
| 방문자 데이터가 끝없이 쌓임 | 서버를 켤 때 7일(`PUBLIC_RETENTION_DAYS`) 넘게 손대지 않은 세션·계획·로그·일정 삭제 |

- 상한은 환경 변수로: `PUBLIC_CHAT_PER_HOUR`, `PUBLIC_CHAT_PER_DAY`, `PUBLIC_UPLOAD_PER_HOUR` (0이면 상한 없음). 서버를 다시 켜면 횟수는 처음부터.
- DB는 WAL 모드라 `data/public.db` 옆에 `-wal`·`-shm` 파일이 생긴다 (정상).
- 화면의 "모든 계획 보기" 토글은 공개 모드에서 숨는다 (`/health`의 `public`).

## 공개 후 확인할 것

- [ ] 밖(휴대폰 LTE)에서 Pages 주소 → 진료실이 뜨고 예시 하나가 끝까지 돈다.
- [ ] 다른 기기에서 연 화면에 내 계획·일정·로그가 보이지 않는다.
- [ ] 서버 창 로그의 접속 IP가 `127.0.0.1`이 아니면 방문자 IP 구분이 된다(Funnel의 `X-Forwarded-For`를 uvicorn이 읽음). 모두 `127.0.0.1`이면 IP 상한이 사실상 전체 상한 → 시연 중 막히면 `PUBLIC_CHAT_PER_HOUR`를 올린다.
- [ ] 이 Mac에서 Pages 화면을 열면 Chrome이 "로컬 네트워크 기기 접근 허용?"을 물을 수 있다 → 허용 (밖의 방문자에게는 묻지 않음).
- [ ] 끝나면 `tailscale funnel reset`.

## 문제 생길 때

| 증상 | 확인 |
|---|---|
| Pages 화면은 뜨는데 "서버에 닿지 않네요" | Mac 서버(`curl -s 127.0.0.1:8010/health`), `tailscale funnel status`, 저장소 변수 `API_BASE_URL` |
| 대화가 막히고 콘솔에 CORS 오류 | 서버의 `ALLOWED_ORIGINS`에 Pages 주소(끝 `/` 없이)가 있는지 |
| "설정 필요" (API 키) | Mac `.env`의 GMS 값, 서버 다시 켜기 |
| "진료 대기가 길어졌네요" | 상한. 시간이 지나거나 서버를 다시 켜면 풀림 |
| Pages가 옛 화면 | Actions `pages` 실행 결과, 브라우저 새로고침(캐시) |
| Actions 테스트 실패 | 로컬에서 `.venv/bin/python -m pytest -q` |
