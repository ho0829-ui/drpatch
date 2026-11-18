"""파일 업로드: requirements.txt 내용을 요청 본문 그대로 받는다 (python-multipart 없이).

화면: fetch(`/upload?session_id=...`, {method: "POST", body: file})
"""

from fastapi import APIRouter, HTTPException, Request

from app.agent.session import new_session_id, save_upload
from app.api.schemas import UploadOut
from app.parsing.requirements import parse_bytes

router = APIRouter(tags=["upload"])
MAX_BYTES = 1_000_000


@router.post("/upload", response_model=UploadOut)
async def upload(request: Request, session_id: str | None = None):
    raw = await request.body()
    if not raw:
        raise HTTPException(status_code=400, detail="빈 파일이에요. pip freeze로 만든 requirements.txt를 올려 주세요.")
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="파일이 너무 커요 (1MB까지).")
    session_id = session_id or new_session_id()
    parsed = parse_bytes(raw).to_dict()
    packages = [{"name": p["name"], "version": p["version"]} for p in parsed["packages"]]
    saved = save_upload(session_id, packages, parsed["excluded"], request.app.state.db_path)
    return {"session_id": session_id, "packages": parsed["packages"], "excluded": parsed["excluded"], "saved": saved}
