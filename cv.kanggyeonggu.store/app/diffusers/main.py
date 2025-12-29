# FastAPI 엔트리 + 정적 파일 서빙(/outputs/...)
# + 라우팅 등록입니다.
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.v1.rotues.generate import router as generate_router
from .core.config import OUTPUTS_DIR

app = FastAPI(title="Diffusers API", version="1.0.0")

# outputs 디렉토리 생성
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# outputs 정적 서빙 (로컬 개발/단독 서버에서 편리)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

app.include_router(generate_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"ok": True}
