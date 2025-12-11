"""
NLP Router - FastAPI 라우터
자연어 처리 및 워드클라우드 API
"""
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import base64
import io
import logging
from datetime import datetime
from app.nlp.emma.emma_wordcloud import NLPService
from nltk import FreqDist

logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    tags=["NLP"],
    responses={
        404: {"description": "데이터를 찾을 수 없습니다"},
        500: {"description": "서버 내부 오류"},
    }
)

# 서비스 인스턴스 생성
nlp_service = NLPService()


@router.get(
    "/emma",
    summary="Emma 워드클라우드 생성",
    description="제인 오스틴의 'Emma' 말뭉치를 사용하여 워드클라우드를 생성하고 반환합니다."
)
async def create_emma_wordcloud(
    width: Optional[int] = Query(1000, description="이미지 너비"),
    height: Optional[int] = Query(600, description="이미지 높이"),
    background_color: Optional[str] = Query("white", description="배경색")
) -> Dict[str, Any]:
    """
    Emma 워드클라우드 생성 및 반환
    
    Args:
        width: 이미지 너비 (기본값: 1000)
        height: 이미지 높이 (기본값: 600)
        background_color: 배경색 (기본값: "white")
    
    Returns:
        워드클라우드 이미지 (Base64 인코딩) 및 메타데이터
    """
    try:
        # 1. Emma 말뭉치 로드
        emma_raw = nlp_service.load_corpus_text("gutenberg", "austen-emma.txt")
        if not emma_raw:
            raise HTTPException(status_code=404, detail="Emma 말뭉치를 찾을 수 없습니다.")
        
        # 2. 텍스트 토큰화
        tokens = nlp_service.tokenize_regex(emma_raw)
        
        # 3. 고유명사 추출 및 빈도 분석
        logger.info("고유명사 추출 시작...")
        freq_dist = nlp_service.extract_names_from_text(emma_raw)
        logger.info(f"고유명사 추출 완료: 총 {freq_dist.N()}개, 고유 {len(freq_dist)}개")
        
        # 빈도 분포 확인
        if freq_dist.N() == 0 or len(freq_dist) == 0:
            logger.warning("고유명사가 추출되지 않았습니다. 전체 단어로 워드클라우드 생성 시도...")
            # 고유명사가 없으면 전체 단어로 시도
            tokens = nlp_service.tokenize_regex(emma_raw)
            freq_dist = nlp_service.create_freq_dist(tokens)
            logger.info(f"전체 단어 빈도 분포: 총 {freq_dist.N()}개, 고유 {len(freq_dist)}개")
        
        if freq_dist.N() == 0 or len(freq_dist) == 0:
            raise HTTPException(
                status_code=500, 
                detail="빈도 분포 데이터가 없어 워드클라우드를 생성할 수 없습니다."
            )
        
        # 4. 워드클라우드 생성
        logger.info("워드클라우드 생성 시작...")
        try:
            wordcloud = nlp_service.generate_wordcloud(
                freq_dist=freq_dist,
                width=width,
                height=height,
                background_color=background_color,
                random_state=0
            )
        except Exception as e:
            logger.error(f"워드클라우드 생성 중 예외 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"워드클라우드 생성 중 오류 발생: {str(e)}"
            )
        
        if not wordcloud:
            logger.error("워드클라우드 객체가 None입니다.")
            raise HTTPException(
                status_code=500, 
                detail="워드클라우드 생성에 실패했습니다. (wordcloud 객체가 None)"
            )
        
        logger.info("워드클라우드 생성 완료")
        
        # 5. save 폴더에 이미지 저장 (덮어쓰기 방식)
        save_path = Path(__file__).parent / "save"
        save_path.mkdir(parents=True, exist_ok=True)
        
        # 고정된 파일명 사용 (기존 파일이 있으면 덮어쓰기)
        filename = "emma_wordcloud.png"
        file_path = save_path / filename
        
        # 기존 파일 확인 로그
        if file_path.exists():
            logger.info(f"기존 파일 발견. 덮어쓰기: {file_path}")
        else:
            logger.info(f"새 파일 생성: {file_path}")
        
        # 이미지 저장 (덮어쓰기)
        try:
            wordcloud.to_file(str(file_path))
            logger.info(f"워드클라우드 저장 완료: {file_path}")
        except Exception as e:
            logger.error(f"워드클라우드 저장 중 오류: {e}")
            raise HTTPException(status_code=500, detail=f"파일 저장 중 오류 발생: {str(e)}")
        
        # 6. 이미지를 Base64로 인코딩
        img_buffer = io.BytesIO()
        wordcloud.to_image().save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # 7. 통계 정보 수집
        most_common = nlp_service.get_most_common(freq_dist, num=10)
        
        return JSONResponse(content={
            "success": True,
            "message": "Emma 워드클라우드 생성 및 저장 완료",
            "image": f"data:image/png;base64,{img_base64}",
            "file_path": str(file_path),
            "file_name": filename,
            "statistics": {
                "total_names": freq_dist.N(),
                "unique_names": len(freq_dist),
                "top_10_names": [
                    {"name": name, "count": count} 
                    for name, count in most_common
                ]
            },
            "settings": {
                "width": width,
                "height": height,
                "background_color": background_color
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"워드클라우드 생성 중 오류 발생: {str(e)}"
        )
