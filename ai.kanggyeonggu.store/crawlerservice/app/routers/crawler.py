"""
크롤러 관련 라우터
"""
from fastapi import APIRouter, HTTPException
from common.utils import create_response, create_error_response
from common.exceptions import ServiceException
import sys
from pathlib import Path

# 상대 경로로 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from bs_demo.bugsmusic import crawl_bugs_chart

router = APIRouter(prefix="/crawler", tags=["crawler"])


@router.get("/")
async def crawler_root():
    """크롤러 서비스 루트"""
    return create_response(
        data={"service": "crawlerservice", "status": "running"},
        message="Crawler Service is running"
    )


@router.get("/bugsmusic")
async def get_bugs_music_chart():
    """
    벅스뮤직 실시간 차트를 크롤링하여 반환
    """
    try:
        chart_data = crawl_bugs_chart()
        
        if not chart_data:
            raise ServiceException("차트 데이터를 가져올 수 없습니다.")
        
        result = {
            "chart_type": "bugs_realtime",
            "total_count": len(chart_data),
            "songs": chart_data
        }
        
        return create_response(
            data=result,
            message="벅스뮤직 차트 조회 성공"
        )
    except Exception as e:
        return create_error_response(
            message=f"크롤링 중 오류 발생: {str(e)}",
            error_code="CRAWL_ERROR"
        )

