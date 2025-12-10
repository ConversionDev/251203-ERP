"""
Seoul Router - FastAPI 라우터
"""
from typing import Dict, Any
from fastapi import APIRouter
from app.seoul_crime.save.seoul_service import SeoulService

# 라우터 생성
router = APIRouter(tags=["Seoul"])

# 서비스 인스턴스 생성
seoul_service = SeoulService()


@router.get(
    "/ml/cctv-5",
    response_model=Dict[str, Any],
    summary="CCTV 데이터 상위 5개 조회",
    description="서울시 자치구별 CCTV 설치현황 데이터 상위 5개를 반환합니다."
)
async def get_cctv_top5():
    """CCTV 데이터 상위 5개 조회"""
    return seoul_service.get_cctv_top5()


@router.get(
    "/ml/crime-5",
    response_model=Dict[str, Any],
    summary="범죄 데이터 상위 5개 조회",
    description="서울시 자치구별 5대 범죄 발생현황 데이터 상위 5개를 반환합니다."
)
async def get_crime_top5():
    """범죄 데이터 상위 5개 조회"""
    return seoul_service.get_crime_top5()


@router.get(
    "/ml/pop-5",
    response_model=Dict[str, Any],
    summary="인구 데이터 상위 5개 조회",
    description="서울시 자치구별 인구 데이터 상위 5개를 반환합니다."
)
async def get_pop_top5():
    """인구 데이터 상위 5개 조회"""
    return seoul_service.get_pop_top5()


@router.get(
    "/ml/preprocess",
    response_model=Dict[str, Any],
    summary="데이터 전처리 및 머지",
    description="CCTV, 범죄, 인구 데이터를 로드하고 CCTV-POP 머지를 수행합니다."
)
async def preprocess():
    """데이터 전처리 및 머지"""
    return seoul_service.preprocess()


@router.get(
    "/ml/cctv-pop-merged",
    response_model=Dict[str, Any],
    summary="CCTV-POP 머지 데이터 조회",
    description="CCTV와 인구 데이터를 머지한 결과를 반환합니다."
)
async def get_cctv_pop_merged(limit: int = 5):
    """CCTV-POP 머지 데이터 조회"""
    return seoul_service.get_cctv_pop_merged(limit=limit)


@router.get(
    "/ml/pop-edited",
    response_model=Dict[str, Any],
    summary="POP 데이터 편집 결과 조회",
    description="POP 데이터에서 컬럼과 행을 삭제한 결과를 반환합니다."
)
async def get_pop_edited(limit: int = 10):
    """POP 데이터 편집 결과 조회"""
    return seoul_service.get_pop_edited(limit=limit)

