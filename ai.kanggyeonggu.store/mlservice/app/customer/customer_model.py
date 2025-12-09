"""
Customer Model - Pydantic 모델
B2B ERP 고객 데이터 모델
"""
from typing import Optional
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """고객 기본 정보"""
    customer_id: str = Field(..., description="고객 ID (예: CUST-001)")
    company_name: str = Field(..., description="회사명")
    email: str = Field(..., description="이메일")
    phone: str = Field(..., description="전화번호")
    company_type: str = Field(..., description="기업 유형 (기업/개인)")
    status: str = Field(..., description="상태 (활성/비활성)")
    
    class Config:
        from_attributes = True


class CustomerDetail(CustomerBase):
    """고객 상세 정보 (통계 포함)"""
    total_orders: int = Field(..., description="총 주문 수")
    total_revenue: int = Field(..., description="총 매출 (원)")
    avg_order_value: int = Field(..., description="평균 주문 금액")
    last_order_days: int = Field(..., description="마지막 주문 후 경과일")
    contract_months: int = Field(..., description="계약 기간 (개월)")
    employee_count: int = Field(..., description="직원 수")
    industry: str = Field(..., description="업종")
    region: str = Field(..., description="지역")
    payment_terms: str = Field(..., description="결제 조건")
    credit_limit: int = Field(..., description="신용 한도")
    overdue_count: int = Field(..., description="연체 횟수")
    response_time_hours: float = Field(..., description="평균 응답 시간 (시간)")
    meeting_count: int = Field(..., description="미팅 횟수")
    support_tickets: int = Field(..., description="지원 티켓 수")
    annual_growth_rate: float = Field(..., description="연간 성장률 (%)")
    churn_risk: int = Field(..., description="이탈 위험도 (0=안전, 1=위험)")


class CustomerSimple(BaseModel):
    """고객 간단 정보 (화면 표시용)"""
    customer_id: str = Field(..., description="고객 ID")
    company_name: str = Field(..., description="회사명")
    status: str = Field(..., description="상태")
    total_orders: int = Field(..., description="총 주문")
    total_revenue: int = Field(..., description="총 매출")
    churn_risk: str = Field(..., description="이탈 위험 (안전/위험)")
    
    class Config:
        from_attributes = True


class CustomerStatistics(BaseModel):
    """고객 통계 정보"""
    total_customers: int = Field(..., description="전체 고객 수")
    active_customers: int = Field(..., description="활성 고객 수")
    inactive_customers: int = Field(..., description="비활성 고객 수")
    high_risk_customers: int = Field(..., description="이탈 위험 고객 수")
    total_revenue: int = Field(..., description="전체 매출")
    avg_revenue_per_customer: float = Field(..., description="고객당 평균 매출")
    avg_orders_per_customer: float = Field(..., description="고객당 평균 주문 수")


class IndustryStatistics(BaseModel):
    """업종별 통계"""
    industry: str = Field(..., description="업종")
    customer_count: int = Field(..., description="고객 수")
    total_revenue: int = Field(..., description="총 매출")
    avg_revenue: float = Field(..., description="평균 매출")
    churn_rate: float = Field(..., description="이탈률 (%)")


class ChurnPrediction(BaseModel):
    """이탈 예측 결과"""
    customer_id: str = Field(..., description="고객 ID")
    company_name: str = Field(..., description="회사명")
    churn_probability: float = Field(..., description="이탈 확률 (0~1)")
    risk_level: str = Field(..., description="위험도 (low/medium/high)")
    key_factors: list[str] = Field(..., description="주요 이탈 요인")
    recommendations: list[str] = Field(..., description="권장 조치")


class CustomerModel:
    """고객 모델 (ML 모델 래퍼)"""
    
    def __init__(self) -> None:
        """초기화"""
        self.model = None
        self.scaler = None
        self.feature_names = [
            'total_orders', 'total_revenue', 'avg_order_value',
            'last_order_days', 'contract_months', 'employee_count',
            'overdue_count', 'response_time_hours', 'meeting_count',
            'support_tickets', 'annual_growth_rate'
        ]
    
    def load_model(self, model_path: str = None):
        """모델 로드"""
        # TODO: joblib.load()로 학습된 모델 로드
        pass
    
    def predict_churn(self, customer_data: dict) -> float:
        """이탈 확률 예측"""
        # TODO: 실제 모델 예측 구현
        # 임시로 규칙 기반 예측
        score = 0.0
        
        # 마지막 주문 후 90일 이상 → +0.3
        if customer_data.get('last_order_days', 0) > 90:
            score += 0.3
        
        # 연체 4회 이상 → +0.2
        if customer_data.get('overdue_count', 0) >= 4:
            score += 0.2
        
        # 성장률 마이너스 → +0.2
        if customer_data.get('annual_growth_rate', 0) < 0:
            score += 0.2
        
        # 지원 티켓 15개 이상 → +0.2
        if customer_data.get('support_tickets', 0) >= 15:
            score += 0.2
        
        # 응답 시간 10시간 이상 → +0.1
        if customer_data.get('response_time_hours', 0) >= 10:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_risk_level(self, probability: float) -> str:
        """위험도 레벨 반환"""
        if probability >= 0.7:
            return "high"
        elif probability >= 0.4:
            return "medium"
        else:
            return "low"
    
    def get_key_factors(self, customer_data: dict) -> list[str]:
        """주요 이탈 요인 분석"""
        factors = []
        
        if customer_data.get('last_order_days', 0) > 90:
            factors.append(f"마지막 주문 후 {customer_data['last_order_days']}일 경과")
        
        if customer_data.get('overdue_count', 0) >= 4:
            factors.append(f"연체 {customer_data['overdue_count']}회 발생")
        
        if customer_data.get('annual_growth_rate', 0) < 0:
            factors.append(f"연간 성장률 {customer_data['annual_growth_rate']}% (마이너스)")
        
        if customer_data.get('support_tickets', 0) >= 15:
            factors.append(f"지원 티켓 {customer_data['support_tickets']}개 (높음)")
        
        if customer_data.get('response_time_hours', 0) >= 10:
            factors.append(f"평균 응답 시간 {customer_data['response_time_hours']}시간 (느림)")
        
        return factors if factors else ["특이사항 없음"]
    
    def get_recommendations(self, risk_level: str, factors: list[str]) -> list[str]:
        """권장 조치 생성"""
        recommendations = []
        
        if risk_level == "high":
            recommendations.append("🚨 즉시 담당자 미팅 일정 잡기")
            recommendations.append("💰 특별 할인 또는 프로모션 제안")
            recommendations.append("📞 주간 단위 정기 연락")
        elif risk_level == "medium":
            recommendations.append("⚠️ 2주 내 담당자 연락")
            recommendations.append("📊 고객 만족도 조사 실시")
            recommendations.append("🎁 소규모 혜택 제공")
        else:
            recommendations.append("✅ 현재 관계 유지")
            recommendations.append("📈 분기별 정기 미팅")
        
        # 요인별 맞춤 조치
        for factor in factors:
            if "주문" in factor:
                recommendations.append("🛒 신규 제품 소개 또는 재주문 유도")
            if "연체" in factor:
                recommendations.append("💳 결제 조건 재협상 또는 분할 납부 제안")
            if "성장률" in factor:
                recommendations.append("📈 비즈니스 확장 지원 프로그램 안내")
            if "티켓" in factor:
                recommendations.append("🔧 전담 기술 지원팀 배정")
            if "응답" in factor:
                recommendations.append("⚡ 우선 응답 서비스 제공")
        
        return list(set(recommendations))  # 중복 제거

