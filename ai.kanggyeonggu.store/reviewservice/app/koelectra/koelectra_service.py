"""
KoELECTRA 감성분석 서비스
"""
import logging
import torch
from pathlib import Path
from typing import Dict, Any, Optional
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModel,
    ElectraForSequenceClassification
)
import numpy as np

logger = logging.getLogger(__name__)


class KoELECTRASentimentService:
    """KoELECTRA 모델을 사용한 감성분석 서비스"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        초기화
        
        Args:
            model_path: 모델 파일 경로 (None이면 기본 경로 사용)
        """
        if model_path is None:
            # 기본 모델 경로 설정
            base_dir = Path(__file__).parent
            model_path = base_dir / "model"
        
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        logger.info(f"KoELECTRA 서비스 초기화 - 모델 경로: {model_path}, 디바이스: {self.device}")
    
    def load_model(self):
        """모델과 토크나이저 로드"""
        if self.is_loaded:
            logger.info("모델이 이미 로드되어 있습니다.")
            return
        
        try:
            logger.info(f"모델 로딩 시작: {self.model_path}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            logger.info("토크나이저 로드 완료")
            
            # 모델 로드 시도
            # 먼저 SequenceClassification으로 시도
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    str(self.model_path),
                    local_files_only=True
                )
                logger.info("AutoModelForSequenceClassification으로 모델 로드 완료")
            except Exception as e:
                logger.warning(f"SequenceClassification 로드 실패: {e}")
                # 일반 모델로 로드 후 분류 헤드 추가
                logger.info("일반 모델로 로드 시도...")
                base_model = AutoModel.from_pretrained(
                    str(self.model_path),
                    local_files_only=True
                )
                # 분류 헤드 추가 (긍정/부정 2개 클래스)
                self.model = ElectraForSequenceClassification.from_pretrained(
                    str(self.model_path),
                    num_labels=2,
                    local_files_only=True
                )
                logger.info("일반 모델로 로드 후 분류 헤드 추가 완료")
            
            # 모델을 디바이스로 이동
            self.model.to(self.device)
            self.model.eval()  # 평가 모드로 설정
            
            self.is_loaded = True
            logger.info(f"모델 로딩 완료 - 디바이스: {self.device}")
            
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}", exc_info=True)
            raise
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        텍스트의 감성 분석 수행
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감성 분석 결과 딕셔너리
        """
        if not self.is_loaded:
            raise RuntimeError("모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요.")
        
        if not text or not text.strip():
            return {
                "text": text,
                "sentiment": "neutral",
                "label": 0,
                "confidence": 0.0,
                "positive_score": 0.5,
                "negative_score": 0.5
            }
        
        try:
            # 텍스트 토크나이징
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # 디바이스로 이동
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 추론 수행
            with torch.no_grad():
                outputs = self.model(**inputs)
                # outputs가 SequenceClassifierOutput인지 확인
                if hasattr(outputs, 'logits'):
                    logits = outputs.logits
                elif hasattr(outputs, 'last_hidden_state'):
                    # PreTraining 모델인 경우, 마지막 hidden state의 평균을 사용
                    logger.warning("PreTraining 모델 감지 - 분류 헤드가 없습니다. 임시로 hidden state 평균 사용")
                    hidden_state = outputs.last_hidden_state
                    # [CLS] 토큰 사용 또는 평균 풀링
                    pooled_output = hidden_state[:, 0, :]  # [CLS] 토큰
                    # 간단한 분류를 위한 선형 레이어 (임시)
                    # 실제로는 fine-tuning된 분류 헤드가 필요함
                    logits = torch.mean(pooled_output, dim=1, keepdim=True)
                    # 2개 클래스로 확장
                    logits = logits.repeat(1, 2)
                else:
                    raise ValueError(f"모델 출력 형식을 인식할 수 없습니다: {type(outputs)}")
            
            # 소프트맥스로 확률 변환
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            probabilities = probabilities.cpu().numpy()[0]
            
            # 결과 해석
            # 일반적으로: 0 = 부정, 1 = 긍정
            negative_score = float(probabilities[0])
            positive_score = float(probabilities[1]) if len(probabilities) > 1 else 1.0 - negative_score
            
            # 감성 레이블 결정
            if positive_score > negative_score:
                sentiment = "positive"
                label = 1
                confidence = positive_score
            else:
                sentiment = "negative"
                label = 0
                confidence = negative_score
            
            result = {
                "text": text,
                "sentiment": sentiment,
                "label": int(label),
                "confidence": float(confidence),
                "positive_score": float(positive_score),
                "negative_score": float(negative_score)
            }
            
            logger.debug(f"감성 분석 완료: {text[:50]}... -> {sentiment} (신뢰도: {confidence:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"감성 분석 중 오류 발생: {e}", exc_info=True)
            raise


# 싱글톤 인스턴스
_sentiment_service: Optional[KoELECTRASentimentService] = None


def get_sentiment_service() -> KoELECTRASentimentService:
    """감성분석 서비스 싱글톤 인스턴스 반환"""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = KoELECTRASentimentService()
        _sentiment_service.load_model()
    return _sentiment_service

