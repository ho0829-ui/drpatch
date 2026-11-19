#!/usr/bin/env bash
# DR.PATCH(sudo-patch) 한 번에 띄우기: 파이썬 가상환경·패키지 → 화면 빌드 → 서버.
#
#   scripts/serve.sh            로컬 (http://127.0.0.1:8000, 지금까지와 같음)
#   scripts/serve.sh --public   공개 모드 (http://127.0.0.1:8010, 내 데이터만·호출 상한·data/public.db)
#                               → 밖으로 열기: tailscale funnel --bg 8010   닫기: tailscale funnel reset
#
# 포트는 PORT=, DB는 DB_PATH= 로 바꿀 수 있다. API 키는 .env에만 (화면·로그에 찍지 않는다).
set -euo pipefail
cd "$(dirname "$0")/.."

PUBLIC=0
if [ "${1:-}" = "--public" ]; then PUBLIC=1; fi

if [ ! -f .env ]; then
  echo "[!] .env가 없어요. .env.example을 복사해 GMS_KEY 등을 채워 주세요:  cp .env.example .env" >&2
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "[1/3] 파이썬 가상환경 만들기"
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
else
  echo "[1/3] 파이썬 가상환경 있음"
fi

echo "[2/3] 화면 빌드 (frontend/dist)"
if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm ci --silent)
fi
(cd frontend && npm run build --silent)

if [ "$PUBLIC" = "1" ]; then
  PORT="${PORT:-8010}"
  export PUBLIC_MODE=1
  export DB_PATH="${DB_PATH:-data/public.db}"
  echo "[3/3] 공개 모드 서버: http://127.0.0.1:${PORT}  (DB ${DB_PATH})"
  echo "      밖으로 열기:  tailscale funnel --bg ${PORT}"
  echo "      닫기:         tailscale funnel reset"
else
  PORT="${PORT:-8000}"
  echo "[3/3] 로컬 서버: http://127.0.0.1:${PORT}"
fi

exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
