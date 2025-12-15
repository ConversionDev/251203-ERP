"""
KoELECTRA 감성분석 라우터
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.koelectra.koelectra_service import get_sentiment_service

logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/koelectra",
    tags=["KoELECTRA 감성분석"],
    responses={
        404: {"description": "리소스를 찾을 수 없습니다"},
        500: {"description": "서버 내부 오류"},
    }
)


class SentimentRequest(BaseModel):
    """감성분석 요청 모델"""
    text: str = Field(..., description="분석할 텍스트", min_length=1, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "이 영화 정말 재미있고 감동적이에요!"
            }
        }


class SentimentBatchRequest(BaseModel):
    """배치 감성분석 요청 모델"""
    texts: List[str] = Field(..., description="분석할 텍스트 리스트", min_items=1, max_items=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "이 영화 정말 재미있고 감동적이에요!",
                    "별로 재미없고 지루했어요."
                ]
            }
        }


class SentimentResponse(BaseModel):
    """감성분석 응답 모델"""
    text: str = Field(..., description="분석한 텍스트")
    sentiment: str = Field(..., description="감성 (positive/negative/neutral)")
    label: int = Field(..., description="레이블 (0: 부정, 1: 긍정)")
    confidence: float = Field(..., description="신뢰도 (0.0 ~ 1.0)")
    positive_score: float = Field(..., description="긍정 확률")
    negative_score: float = Field(..., description="부정 확률")


class SentimentBatchResponse(BaseModel):
    """배치 감성분석 응답 모델"""
    results: List[SentimentResponse] = Field(..., description="감성분석 결과 리스트")
    total: int = Field(..., description="총 분석 개수")


@router.post(
    "/analyze",
    response_model=SentimentResponse,
    summary="단일 텍스트 감성분석",
    description="입력된 텍스트의 감성을 분석하여 긍정/부정을 판단합니다."
)
async def analyze_sentiment(request: SentimentRequest):
    """
    단일 텍스트 감성분석
    
    - **text**: 분석할 텍스트 (최대 1000자)
    
    반환값:
    - **sentiment**: 감성 (positive/negative/neutral)
    - **label**: 레이블 (0: 부정, 1: 긍정)
    - **confidence**: 신뢰도
    - **positive_score**: 긍정 확률
    - **negative_score**: 부정 확률
    """
    try:
        service = get_sentiment_service()
        result = service.analyze_sentiment(request.text)
        return SentimentResponse(**result)
    except Exception as e:
        logger.error(f"감성분석 오류: {e}", exc_info=True)
        import traceback
        error_detail = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        logger.error(f"상세 오류: {error_detail}")
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "감성분석 중 오류가 발생했습니다",
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


@router.post(
    "/analyze/batch",
    response_model=SentimentBatchResponse,
    summary="배치 텍스트 감성분석",
    description="여러 텍스트를 한 번에 분석하여 감성을 판단합니다."
)
async def analyze_sentiment_batch(request: SentimentBatchRequest):
    """
    배치 텍스트 감성분석
    
    - **texts**: 분석할 텍스트 리스트 (최대 100개)
    
    반환값:
    - **results**: 감성분석 결과 리스트
    - **total**: 총 분석 개수
    """
    try:
        service = get_sentiment_service()
        results = []
        
        for text in request.texts:
            result = service.analyze_sentiment(text)
            results.append(SentimentResponse(**result))
        
        return SentimentBatchResponse(
            results=results,
            total=len(results)
        )
    except Exception as e:
        logger.error(f"배치 감성분석 오류: {e}", exc_info=True)
        import traceback
        error_detail = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        logger.error(f"상세 오류: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "배치 감성분석 중 오류가 발생했습니다",
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


@router.get(
    "/health",
    summary="서비스 상태 확인",
    description="KoELECTRA 감성분석 서비스의 상태를 확인합니다."
)
async def health_check():
    """서비스 상태 확인"""
    try:
        service = get_sentiment_service()
        return {
            "status": "healthy",
            "model_loaded": service.is_loaded,
            "device": str(service.device),
            "model_path": str(service.model_path)
        }
    except Exception as e:
        logger.error(f"헬스체크 오류: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }

