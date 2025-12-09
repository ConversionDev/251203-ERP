"""
Titanic Model - Pydantic 모델
타이타닉 데이터 모델
"""
from typing import Optional
from pydantic import BaseModel, Field


class TitanicPassenger(BaseModel):
    """타이타닉 승객 전체 정보"""
    PassengerId: int = Field(..., description="승객 ID")
    Survived: Optional[int] = Field(None, description="생존 여부 (0=사망, 1=생존)")
    Pclass: int = Field(..., description="객실 등급 (1, 2, 3)")
    Name: str = Field(..., description="승객 이름")
    Sex: str = Field(..., description="성별 (male, female)")
    Age: Optional[float] = Field(None, description="나이")
    SibSp: int = Field(..., description="형제/자매/배우자 수")
    Parch: int = Field(..., description="부모/자녀 수")
    Ticket: str = Field(..., description="티켓 번호")
    Fare: Optional[float] = Field(None, description="요금")
    Cabin: Optional[str] = Field(None, description="객실 번호")
    Embarked: Optional[str] = Field(None, description="승선 항구 (C, Q, S)")
    
    class Config:
        from_attributes = True


class TitanicPassengerSimple(BaseModel):
    """타이타닉 승객 간단 정보 (화면 표시용)"""
    PassengerId: int = Field(..., description="승객 ID")
    Name: str = Field(..., description="승객 이름")
    Age: Optional[float] = Field(None, description="나이")
    Sex: str = Field(..., description="성별 (남성/여성)")
    Pclass: int = Field(..., description="객실 등급")
    Survived: str = Field(..., description="생존 여부 (생존/사망)")
    Fare: Optional[float] = Field(None, description="요금")
    
    class Config:
        from_attributes = True


class TitanicPassengerList(BaseModel):
    """타이타닉 승객 목록"""
    passengers: list[TitanicPassenger] = Field(..., description="승객 목록")
    total: int = Field(..., description="전체 승객 수")
    
    class Config:
        from_attributes = True


class TitanicModel:
    """타이타닉 모델 (ML 모델 래퍼)"""

    def __init__(self) -> None:
        """초기화"""
        self.model = None
        self.scaler = None
        pass
