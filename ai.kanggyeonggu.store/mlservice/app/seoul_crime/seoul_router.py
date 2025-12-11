"""
Seoul Router - FastAPI 라우터
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.seoul_crime.seoul_service import SeoulService

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
    try:
        return seoul_service.get_cctv_top5()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CCTV 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/ml/crime-5",
    response_model=Dict[str, Any],
    summary="범죄 데이터 상위 5개 조회",
    description="서울시 자치구별 5대 범죄 발생현황 데이터 상위 5개를 반환합니다."
)
async def get_crime_top5():
    """범죄 데이터 상위 5개 조회"""
    try:
        return seoul_service.get_crime_top5()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"범죄 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/ml/pop-5",
    response_model=Dict[str, Any],
    summary="인구 데이터 상위 5개 조회",
    description="서울시 자치구별 인구 데이터 상위 5개를 반환합니다."
)
async def get_pop_top5():
    """인구 데이터 상위 5개 조회"""
    try:
        return seoul_service.get_pop_top5()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"인구 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/ml/preprocess",
    response_model=Dict[str, Any],
    summary="데이터 전처리 및 머지",
    description="CCTV, 범죄, 인구 데이터를 로드하고 CCTV-POP 머지를 수행합니다."
)
async def preprocess():
    """데이터 전처리 및 머지"""
    try:
        return seoul_service.preprocess()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"데이터 전처리 중 오류 발생: {str(e)}"
        )


@router.get(
    "/ml/cctv-pop-merged",
    response_model=Dict[str, Any],
    summary="CCTV-POP 머지 데이터 조회",
    description="CCTV와 인구 데이터를 머지한 결과를 반환합니다."
)
async def get_cctv_pop_merged(limit: int = 5):
    """CCTV-POP 머지 데이터 조회"""
    try:
        return seoul_service.get_cctv_pop_merged(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CCTV-POP 머지 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/ml/pop-edited",
    response_model=Dict[str, Any],
    summary="POP 데이터 편집 결과 조회",
    description="POP 데이터에서 컬럼과 행을 삭제한 결과를 반환합니다."
)
async def get_pop_edited(limit: int = 10):
    """POP 데이터 편집 결과 조회"""
    try:
        return seoul_service.get_pop_edited(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"POP 데이터 편집 결과 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/ml/map",
    summary="범죄율 지도 HTML 반환",
    description="서울시 자치구별 범죄율 지도 HTML을 반환합니다. 항상 최신 코드로 재생성됩니다.",
    response_class=HTMLResponse
)
async def get_crime_rate_map():
    """
    범죄율 지도 HTML 반환
    
    항상 최신 코드로 지도를 재생성하여 반환합니다.
    save 폴더에 seoul_crime.html로 저장됩니다.
    """
    try:
        # 데이터 전처리
        seoul_service.preprocess()
        
        # 데이터셋에서 데이터 가져오기
        crime_df = seoul_service.method.dataset.crime
        pop_df = seoul_service.method.dataset.pop
        
        # save 폴더 경로 설정
        from pathlib import Path
        save_path = Path(__file__).parent.parent / "seoul_crime" / "save"
        save_path.mkdir(parents=True, exist_ok=True)
        
        # 지도 HTML 생성 (save_path 전달하여 파일 저장)
        html_str = seoul_service.generate_crime_rate_map(crime_df, pop_df, save_path)
        
        return HTMLResponse(content=html_str)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"지도 생성 중 오류 발생: {str(e)}"
        )

