"""
Auth Service 설정
"""
from common.config import BaseServiceConfig


class AuthServiceConfig(BaseServiceConfig):
    """인증 서비스 설정"""
    service_name: str = "authservice"
    service_version: str = "1.0.0"
    port: int = 9002
    
    class Config:
        env_file = ".env"
        case_sensitive = False

