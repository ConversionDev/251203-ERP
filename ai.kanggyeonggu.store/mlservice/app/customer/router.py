"""
Customer Router - FastAPI 라우터
B2B ERP 고객 관리 API
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.customer.customer_service import CustomerService
from app.customer.customer_model import (
    CustomerDetail, CustomerSimple, CustomerStatistics,
    IndustryStatistics, ChurnPrediction
)

# 라우터 생성
router = APIRouter(
    tags=["Customer"],
    responses={
        404: {"description": "데이터를 찾을 수 없습니다"},
        500: {"description": "서버 내부 오류"},
    }
)

# 서비스 인스턴스 생성
customer_service = CustomerService()


# ============================================================================
# 1. 고객 데이터 조회 (CRUD)
# ============================================================================

@router.get(
    "/customers/simple",
    response_model=List[CustomerSimple],
    summary="고객 목록 조회 (간단 버전)",
    description="""
    고객 목록을 **간단하게** 조회합니다. (화면 표시용)
    
    ### 포함 정보
    - 고객 ID, 회사명, 상태, 총 주문, 총 매출, 이탈 위험
    
    ### Parameters
    - **limit**: 조회할 최대 고객 수 (기본값: 전체)
    
    ### Example Response
    ```json
    [
        {
            "customer_id": "CUST-001",
            "company_name": "ABC 기업",
            "status": "활성",
            "total_orders": 15,
            "total_revenue": 45000000,
            "churn_risk": "안전"
        }
    ]
    ```
    """,
    response_description="고객 목록 (간단 버전)"
)
async def get_customers_simple(
    limit: Optional[int] = Query(None, description="조회할 최대 고객 수")
):
    """고객 목록 조회 (간단 버전)"""
    try:
        customers = customer_service.get_customers_simple(limit=limit)
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get(
    "/customers",
    response_model=List[CustomerDetail],
    summary="고객 목록 조회 (전체 정보)",
    description="""
    고객 목록을 **전체** 조회합니다.
    
    ### Parameters
    - **limit**: 조회할 최대 고객 수 (기본값: 전체)
    
    ### Returns
    - 모든 고객 정보를 포함한 리스트 (22개 필드)
    """,
    response_description="고객 목록 (전체 정보)"
)
async def get_all_customers(
    limit: Optional[int] = Query(None, description="조회할 최대 고객 수")
):
    """고객 목록 조회 (전체 정보)"""
    try:
        customers = customer_service.get_all_customers(limit=limit)
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerDetail,
    summary="고객 상세 조회",
    description="""
    특정 고객의 상세 정보를 조회합니다.
    
    ### Parameters
    - **customer_id**: 고객 ID (예: CUST-001)
    
    ### Returns
    - 고객의 모든 정보 (22개 필드)
    """,
    response_description="고객 상세 정보"
)
async def get_customer_by_id(customer_id: str):
    """고객 ID로 조회"""
    try:
        customer = customer_service.get_customer_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"고객 {customer_id}를 찾을 수 없습니다")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 오류: {str(e)}")


@router.get(
    "/customers/filter/status",
    response_model=List[CustomerDetail],
    summary="상태별 고객 필터링",
    description="""
    고객을 상태별로 필터링합니다.
    
    ### Parameters
    - **status**: 상태 (활성/비활성)
    
    ### Returns
    - 해당 상태의 고객 목록
    """,
    response_description="필터링된 고객 목록"
)
async def filter_by_status(
    status: str = Query(..., description="상태 (활성/비활성)", enum=["활성", "비활성"])
):
    """상태별 필터링"""
    try:
        customers = customer_service.filter_by_status(status)
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"필터링 오류: {str(e)}")


@router.get(
    "/customers/filter/industry",
    response_model=List[CustomerDetail],
    summary="업종별 고객 필터링",
    description="""
    고객을 업종별로 필터링합니다.
    
    ### Parameters
    - **industry**: 업종 (제조업/IT/유통/건설/서비스/금융)
    
    ### Returns
    - 해당 업종의 고객 목록
    """,
    response_description="필터링된 고객 목록"
)
async def filter_by_industry(
    industry: str = Query(..., description="업종", enum=["제조업", "IT", "유통", "건설", "서비스", "금융"])
):
    """업종별 필터링"""
    try:
        customers = customer_service.filter_by_industry(industry)
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"필터링 오류: {str(e)}")


@router.get(
    "/customers/filter/churn-risk",
    response_model=List[CustomerDetail],
    summary="이탈 위험도별 고객 필터링",
    description="""
    고객을 이탈 위험도별로 필터링합니다.
    
    ### Parameters
    - **risk**: 이탈 위험도 (0=안전, 1=위험)
    
    ### Returns
    - 해당 위험도의 고객 목록
    """,
    response_description="필터링된 고객 목록"
)
async def filter_by_churn_risk(
    risk: int = Query(..., description="이탈 위험도 (0=안전, 1=위험)", enum=[0, 1])
):
    """이탈 위험도별 필터링"""
    try:
        customers = customer_service.filter_by_churn_risk(risk)
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"필터링 오류: {str(e)}")


# ============================================================================
# 2. 통계 분석
# ============================================================================

@router.get(
    "/statistics/overview",
    response_model=CustomerStatistics,
    summary="전체 고객 통계",
    description="""
    전체 고객의 통계 정보를 조회합니다.
    
    ### Returns
    - 전체 고객 수
    - 활성/비활성 고객 수
    - 이탈 위험 고객 수
    - 총 매출
    - 고객당 평균 매출
    - 고객당 평균 주문 수
    
    ### Example Response
    ```json
    {
        "total_customers": 30,
        "active_customers": 23,
        "inactive_customers": 7,
        "high_risk_customers": 7,
        "total_revenue": 1663000000,
        "avg_revenue_per_customer": 55433333.33,
        "avg_orders_per_customer": 12.5
    }
    ```
    """,
    response_description="전체 고객 통계"
)
async def get_statistics():
    """전체 고객 통계"""
    try:
        stats = customer_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 계산 오류: {str(e)}")


@router.get(
    "/statistics/industry",
    response_model=List[IndustryStatistics],
    summary="업종별 통계",
    description="""
    업종별 통계 정보를 조회합니다.
    
    ### Returns
    - 업종별 고객 수
    - 업종별 총 매출
    - 업종별 평균 매출
    - 업종별 이탈률
    
    ### Example Response
    ```json
    [
        {
            "industry": "제조업",
            "customer_count": 7,
            "total_revenue": 350000000,
            "avg_revenue": 50000000.0,
            "churn_rate": 14.3
        }
    ]
    ```
    """,
    response_description="업종별 통계"
)
async def get_industry_statistics():
    """업종별 통계"""
    try:
        stats = customer_service.get_industry_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 계산 오류: {str(e)}")


@router.get(
    "/statistics/top-customers",
    response_model=List[CustomerDetail],
    summary="상위 고객 조회",
    description="""
    상위 고객을 조회합니다.
    
    ### Parameters
    - **limit**: 조회할 고객 수 (기본값: 10)
    - **by**: 정렬 기준 (revenue=매출, orders=주문 수)
    
    ### Returns
    - 상위 고객 목록
    """,
    response_description="상위 고객 목록"
)
async def get_top_customers(
    limit: int = Query(10, description="조회할 고객 수"),
    by: str = Query("revenue", description="정렬 기준", enum=["revenue", "orders"])
):
    """상위 고객 조회"""
    try:
        customers = customer_service.get_top_customers(limit=limit, by=by)
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 오류: {str(e)}")


# ============================================================================
# 3. 데이터 분석 (Pandas, NumPy)
# ============================================================================

@router.get(
    "/dataset/preprocess",
    response_model=Dict[str, Any],
    summary="데이터 전처리 정보",
    description="""
    데이터 전처리 정보를 조회합니다.
    
    ### Returns
    - 전체 행 수
    - 수치형 특성 목록
    - 범주형 특성 목록
    - 결측치 정보
    - 타겟 변수
    """,
    response_description="전처리 정보"
)
async def get_preprocess_info():
    """데이터 전처리 정보"""
    try:
        info = customer_service.preprocess()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전처리 오류: {str(e)}")


@router.get(
    "/dataset/split",
    response_model=Dict[str, Any],
    summary="학습/테스트 데이터 분할 정보",
    description="""
    학습/테스트 데이터 분할 정보를 조회합니다.
    
    ### Parameters
    - **test_size**: 테스트 데이터 비율 (기본값: 0.2)
    
    ### Returns
    - 학습 데이터 크기
    - 테스트 데이터 크기
    - 학습 데이터 이탈률
    - 테스트 데이터 이탈률
    - 특성 목록
    """,
    response_description="데이터 분할 정보"
)
async def get_split_info(
    test_size: float = Query(0.2, description="테스트 데이터 비율", ge=0.1, le=0.5)
):
    """학습/테스트 데이터 분할 정보"""
    try:
        info = customer_service.split_data(test_size=test_size)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 분할 오류: {str(e)}")


# ============================================================================
# 4. 머신러닝 (Scikit-learn)
# ============================================================================

@router.post(
    "/ml/train",
    response_model=Dict[str, Any],
    summary="이탈 예측 모델 학습",
    description="""
    이탈 예측 모델을 학습합니다.
    
    ### Returns
    - 모델 타입
    - 정확도
    - 학습 데이터 크기
    - 테스트 데이터 크기
    - 특성 중요도
    
    ### Example Response
    ```json
    {
        "model_type": "RandomForestClassifier",
        "accuracy": 0.85,
        "train_size": 24,
        "test_size": 6,
        "feature_importance": {
            "last_order_days": 0.25,
            "overdue_count": 0.20,
            ...
        }
    }
    ```
    """,
    response_description="모델 학습 결과"
)
async def train_model():
    """이탈 예측 모델 학습"""
    try:
        result = customer_service.train_model()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델 학습 오류: {str(e)}")


@router.get(
    "/ml/predict/{customer_id}",
    response_model=ChurnPrediction,
    summary="고객 이탈 확률 예측",
    description="""
    특정 고객의 이탈 확률을 예측합니다.
    
    ### Parameters
    - **customer_id**: 고객 ID (예: CUST-001)
    
    ### Returns
    - 고객 ID
    - 회사명
    - 이탈 확률 (0~1)
    - 위험도 (low/medium/high)
    - 주요 이탈 요인
    - 권장 조치
    
    ### Example Response
    ```json
    {
        "customer_id": "CUST-005",
        "company_name": "JKL 회사",
        "churn_probability": 0.9,
        "risk_level": "high",
        "key_factors": [
            "마지막 주문 후 120일 경과",
            "연체 5회 발생",
            "연간 성장률 -5.2% (마이너스)"
        ],
        "recommendations": [
            "🚨 즉시 담당자 미팅 일정 잡기",
            "💰 특별 할인 또는 프로모션 제안",
            "🛒 신규 제품 소개 또는 재주문 유도"
        ]
    }
    ```
    """,
    response_description="이탈 예측 결과"
)
async def predict_churn(customer_id: str):
    """고객 이탈 확률 예측"""
    try:
        prediction = customer_service.predict_churn(customer_id)
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 오류: {str(e)}")


# ============================================================================
# 5. HuggingFace Datasets
# ============================================================================

@router.get(
    "/dataset/huggingface",
    response_model=Dict[str, Any],
    summary="HuggingFace Dataset 정보",
    description="""
    HuggingFace Dataset 형식으로 변환된 데이터 정보를 조회합니다.
    
    ### Returns
    - 데이터셋 크기
    - 특성 목록
    - 샘플 데이터
    """,
    response_description="HuggingFace Dataset 정보"
)
async def get_huggingface_dataset():
    """HuggingFace Dataset 정보"""
    try:
        dataset = customer_service.to_huggingface_dataset()
        return {
            "num_rows": len(dataset),
            "num_columns": len(dataset.column_names),
            "column_names": dataset.column_names,
            "features": str(dataset.features),
            "sample": dataset[0] if len(dataset) > 0 else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset 생성 오류: {str(e)}")


@router.get(
    "/dataset/huggingface-dict",
    response_model=Dict[str, Any],
    summary="HuggingFace DatasetDict 정보",
    description="""
    HuggingFace DatasetDict 형식으로 변환된 데이터 정보를 조회합니다.
    (train/test 분할)
    
    ### Parameters
    - **test_size**: 테스트 데이터 비율 (기본값: 0.2)
    
    ### Returns
    - 학습 데이터 크기
    - 테스트 데이터 크기
    - 특성 목록
    """,
    response_description="HuggingFace DatasetDict 정보"
)
async def get_huggingface_datasetdict(
    test_size: float = Query(0.2, description="테스트 데이터 비율", ge=0.1, le=0.5)
):
    """HuggingFace DatasetDict 정보"""
    try:
        dataset_dict = customer_service.to_huggingface_datasetdict(test_size=test_size)
        return {
            "train_size": len(dataset_dict['train']),
            "test_size": len(dataset_dict['test']),
            "column_names": dataset_dict['train'].column_names,
            "features": str(dataset_dict['train'].features)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DatasetDict 생성 오류: {str(e)}")

