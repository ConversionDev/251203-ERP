"""
인증 관련 라우터
"""
from fastapi import APIRouter
from common.utils import create_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/")
async def auth_root():
    """인증 서비스 루트"""
    return create_response(
        data={"service": "authservice", "status": "running"},
        message="Auth Service is running"
    )


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return create_response(
        data={"status": "healthy", "service": "authservice"},
        message="Service is healthy"
    )

