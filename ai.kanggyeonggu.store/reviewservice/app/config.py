"""
Review Service 설정
"""
from common.config import BaseServiceConfig


class ReviewServiceConfig(BaseServiceConfig):
    """리뷰 감성분석 서비스 설정"""
    service_name: str = "reviewservice"
    service_version: str = "1.0.0"
    port: int = 9004
    
    class Config:
        env_file = ".env"
        case_sensitive = False

