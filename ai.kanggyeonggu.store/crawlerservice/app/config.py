"""
Crawler Service 설정
"""
from common.config import BaseServiceConfig


class CrawlerServiceConfig(BaseServiceConfig):
    """크롤러 서비스 설정"""
    service_name: str = "crawlerservice"
    service_version: str = "1.0.0"
    port: int = 9001
    
    class Config:
        env_file = ".env"
        case_sensitive = False

