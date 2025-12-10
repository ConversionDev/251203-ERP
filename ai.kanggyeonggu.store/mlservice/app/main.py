"""
ML Service - FastAPI 애플리케이션
타이타닉 데이터셋 분석 및 머신러닝 서비스
"""
import sys
from pathlib import Path
from fastapi import FastAPI

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import TitanicServiceConfig
from common.middleware import LoggingMiddleware
from common.utils import setup_logging
from app.titanic.router import router as titanic_router
from app.customer.router import router as customer_router
from app.seoul_crime.save.seoul_router import router as seoul_router

# 설정 로드
config = TitanicServiceConfig()

# 로깅 설정
logger = setup_logging(config.service_name)

# 루트 로거도 설정하여 모든 모듈의 로그가 출력되도록 함
import logging
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
if not root_logger.handlers:
    handler = logging.StreamHandler()
    # 더 깔끔한 로그 포맷
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

# FastAPI 앱 생성
app = FastAPI(
    title="ML Service API - Titanic Dataset",
    description="""
    ## 타이타닉 데이터셋 분석 및 머신러닝 서비스 API
    
    이 API는 타이타닉 데이터셋을 활용한 다양한 기능을 제공합니다:
    
    ### 주요 기능
    
    #### 1. 승객 데이터 조회 (CRUD)
    - 상위 N명 승객 정보 조회
    - 전체 승객 정보 조회
    - 특정 승객 ID로 조회
    - 생존 여부, 객실 등급, 성별로 필터링
    
    #### 2. 통계 분석
    - 생존율 통계
    - 나이 통계 (평균, 최소, 최대)
    
    #### 3. 데이터 분석 (Pandas, NumPy)
    - 데이터셋 요약 정보
    - 상관관계 매트릭스
    - NumPy 기반 통계 계산
    
    #### 4. 머신러닝 전처리 (Scikit-learn)
    - 데이터 전처리 (결측치 처리, 인코딩, 스케일링)
    - 학습/테스트 데이터 분할
    
    #### 5. HuggingFace Datasets
    - HuggingFace Dataset 형식으로 데이터 로드
    - DatasetDict 생성 및 관리
    
    ### 데이터셋
    - **Train Dataset**: 891명의 승객 정보 (생존 여부 포함)
    - **Test Dataset**: 418명의 승객 정보 (생존 여부 미포함)
    
    ### 사용 라이브러리
    - FastAPI, Pydantic
    - Pandas, NumPy
    - Scikit-learn
    - HuggingFace Datasets
    - Icecream (디버깅)
    
    ### URL 구조
    - **서비스 정보**: `/`, `/health`
    - **API 문서**: `/docs`, `/redoc`
    - **Titanic 도메인**: `/titanic/**`
    """,
    version=config.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Kanggyeonggu ML Service",
        "url": "https://www.kanggyeonggu.store",
    },
    license_info={
        "name": "MIT License",
    },
    tags_metadata=[
        {
            "name": "Service",
            "description": "서비스 기본 정보 및 헬스체크",
        },
        {
            "name": "Titanic",
            "description": "타이타닉 데이터셋 CRUD, 통계, 분석 및 머신러닝 기능",
        },
        {
            "name": "Customer",
            "description": "B2B ERP 고객 관리, 통계, 분석 및 이탈 예측 ML 기능",
        },
        {
            "name": "Seoul",
            "description": "서울시 범죄, CCTV, 인구 데이터 조회 및 분석 기능",
        },
    ]
)

# CORS는 Gateway에서 처리하므로 ML Service에서는 제거
# Gateway를 통해 접근하므로 ML Service 레벨에서는 CORS 미들웨어 불필요

# 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# Titanic 라우터 추가
app.include_router(titanic_router, prefix="/titanic")
# Customer 라우터 추가
app.include_router(customer_router, prefix="/customer")
# Seoul 라우터 추가
app.include_router(seoul_router, prefix="/seoul")


# ============================================================================
# 서비스 레벨 엔드포인트 (공통)
# ============================================================================

@app.get("/", tags=["Service"])
async def root():
    """
    ## 서비스 정보
    
    ML Service의 기본 정보와 사용 가능한 엔드포인트를 반환합니다.
    
    ### Returns
    - **service**: 서비스 이름
    - **version**: 서비스 버전
    - **status**: 서비스 상태
    - **endpoints**: 주요 엔드포인트 목록
    - **documentation**: API 문서 URL
    """
    return {
        "service": config.service_name,
        "version": config.service_version,
        "status": "running",
        "message": "ML Service API - Titanic Dataset Analysis",
        "endpoints": {
            "health": "/health",
            "titanic_data": "/titanic/passengers/top10",
            "titanic_stats": "/titanic/statistics/survival-rate",
            "customer_data": "/customer/customers/simple",
            "customer_stats": "/customer/statistics/overview",
            "customer_predict": "/customer/ml/predict/{customer_id}",
            "documentation": "/docs"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        }
    }


@app.get("/health", tags=["Service"])
async def health_check():
    """
    ## 헬스체크
    
    서비스의 상태를 확인합니다.
    
    ### Returns
    - **status**: 서비스 상태 (healthy/unhealthy)
    - **service**: 서비스 이름
    - **version**: 서비스 버전
    """
    return {
        "status": "healthy",
        "service": config.service_name,
        "version": config.service_version
    }


# ============================================================================
# 이벤트 핸들러
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 실행"""
    logger.info(f"🚀 {config.service_name} v{config.service_version} started")
    logger.info(f"📚 API Documentation: http://localhost:{config.port}/docs")
    logger.info(f"🔍 Health Check: http://localhost:{config.port}/health")


@app.on_event("shutdown")
async def shutdown_event():
    """서비스 종료 시 실행"""
    logger.info(f"🛑 {config.service_name} shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.port)
