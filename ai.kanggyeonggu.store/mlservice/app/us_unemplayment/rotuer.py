"""
US Unemployment Router - FastAPI 라우터
"""
import logging
from typing import Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from app.us_unemplayment.service import USUnemploymentService

logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["USA"])

# 서비스 인스턴스 생성
try:
    usa_service = USUnemploymentService()
    logger.info("US Unemployment Service 인스턴스 생성 성공")
except Exception as e:
    logger.error(f"US Unemployment Service 인스턴스 생성 실패: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="미국 실업률 지도 생성",
    description="미국 주별 실업률 데이터를 지도로 시각화하고 HTML 파일로 저장합니다."
)
async def create_unemployment_map():
    """미국 실업률 지도 생성 및 저장"""
    try:
        import asyncio
        from functools import partial
        from pathlib import Path
        
        logger.info("🦝 지도 생성 요청 시작")
        
        # us-unemplayment 폴더에 저장
        save_path = Path(__file__).parent
        save_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"저장 경로: {save_path}")
        
        html_file = save_path / "us_unemployment_map.html"
        logger.info(f"HTML 파일 경로: {html_file}")
        
        # 동기 함수를 비동기로 실행 (partial로 인자 전달)
        logger.info("지도 생성 시작 (비동기 실행)...")
        loop = asyncio.get_event_loop()
        visualize_func = partial(usa_service.visualize, html_file)
        await loop.run_in_executor(None, visualize_func)
        logger.info("지도 생성 완료")
        
        # 파일 존재 확인
        file_exists = html_file.exists()
        file_size = html_file.stat().st_size if file_exists else 0
        logger.info(f"파일 생성 확인: 존재={file_exists}, 크기={file_size} bytes")
        
        return JSONResponse(content={
            "success": True,
            "message": "미국 실업률 지도 생성 완료",
            "file_path": str(html_file),
            "file_exists": file_exists,
            "file_size": file_size,
            "view_url": "/api/ml/usa/map"
        })
    except Exception as e:
        import traceback
        error_msg = f"지도 생성 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/map",
    summary="생성된 지도 HTML 파일 반환",
    description="생성된 미국 실업률 지도 HTML 파일을 반환합니다."
)
async def get_unemployment_map():
    """생성된 지도 HTML 파일 반환"""
    try:
        import asyncio
        from pathlib import Path
        html_file = Path(__file__).parent / "us_unemployment_map.html"
        
        logger.info(f"지도 파일 요청: {html_file}")
        logger.info(f"파일 존재 여부: {html_file.exists()}")
        
        if not html_file.exists():
            # 파일이 없으면 생성
            logger.info("파일이 없어서 생성 시작...")
            from functools import partial
            html_file.parent.mkdir(parents=True, exist_ok=True)
            loop = asyncio.get_event_loop()
            visualize_func = partial(usa_service.visualize, html_file)
            await loop.run_in_executor(None, visualize_func)
            logger.info("파일 생성 완료")
        else:
            # 파일이 존재하는 경우 크기 확인
            file_size = html_file.stat().st_size
            logger.info(f"기존 파일 사용: 크기={file_size} bytes")
        
        # 파일 존재 최종 확인
        if not html_file.exists():
            raise HTTPException(status_code=404, detail="지도 파일을 찾을 수 없습니다.")
        
        # 파일 읽기 권한 확인
        if not html_file.is_file():
            raise HTTPException(status_code=500, detail="지도 파일이 유효한 파일이 아닙니다.")
        
        logger.info(f"FileResponse 반환: {html_file}")
        return FileResponse(
            path=str(html_file),
            media_type="text/html",
            filename="us_unemployment_map.html"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"지도 파일 반환 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/data",
    response_model=Dict[str, Any],
    summary="실업률 데이터 조회",
    description="미국 주별 실업률 데이터를 반환합니다."
)
async def get_unemployment_data():
    """실업률 데이터 조회"""
    try:
        import asyncio
        # 동기 함수를 비동기로 실행
        loop = asyncio.get_event_loop()
        geo_data = await loop.run_in_executor(None, usa_service.load_geo_data)
        unemployment_data = await loop.run_in_executor(None, usa_service.load_unemployment_data)
        
        return JSONResponse(content={
            "success": True,
            "geo_data_keys": list(geo_data.keys()) if isinstance(geo_data, dict) else "N/A",
            "unemployment_data": unemployment_data.to_dict(orient="records"),
            "data_shape": {
                "rows": len(unemployment_data),
                "columns": len(unemployment_data.columns)
            }
        })
    except Exception as e:
        import traceback
        error_msg = f"데이터 조회 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

