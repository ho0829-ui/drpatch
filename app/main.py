"""sudo-patch 백엔드 진입점.

    uvicorn app.main:app --reload   →  http://localhost:8000

구조는 1일차 FastAPI 실습과 같다: 이 파일은 앱을 만들고 라우터를 붙이기만 한다.
라우터(/upload, /chat, /plans, /logs)는 spec "백엔드 API" 순서대로 app/api/ 에 하나씩 추가한다.
화면(HTML/CSS/JS)도 이 서버가 같이 내보낼 예정이라(같은 주소) CORS 설정은 두지 않는다.
"""

from fastapi import FastAPI

app = FastAPI(title="sudo-patch", description="서버 패치·EOL 점검 플래너")


@app.get("/health")
def health() -> dict:
    """서버가 켜져 있는지만 확인한다."""
    return {"ok": True}
