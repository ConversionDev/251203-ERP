"""
Review Service - FastAPI 애플리케이션
영화 리뷰 감성분석 서비스
"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import ReviewServiceConfig
from app.koelectra.koelectra_router import router as koelectra_router
from common.middleware import LoggingMiddleware
from common.utils import setup_logging

# 설정 로드
config = ReviewServiceConfig()

# 로깅 설정
logger = setup_logging(config.service_name)

# FastAPI 앱 생성
app = FastAPI(
    title="Review Service API",
    description="영화 리뷰 감성분석 서비스 API 문서",
    version=config.service_version
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# 라우터 등록
app.include_router(koelectra_router)


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 실행"""
    logger.info(f"{config.service_name} v{config.service_version} started")
    logger.info("KoELECTRA 모델 로딩 시작...")
    
    # 모델 로드 (지연 로딩 방식이므로 첫 요청 시 로드됨)
    try:
        from app.koelectra.koelectra_service import get_sentiment_service
        service = get_sentiment_service()
        logger.info("KoELECTRA 모델 로딩 완료")
    except Exception as e:
        logger.error(f"KoELECTRA 모델 로딩 실패: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """서비스 종료 시 실행"""
    logger.info(f"{config.service_name} shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.port)

