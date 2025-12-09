"""
Titanic Router - FastAPI 라우터
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.titanic.titanic_service import TitanicService
from app.titanic.titanic_model import TitanicPassenger, TitanicPassengerSimple

# 라우터 생성
router = APIRouter(
    tags=["Titanic"],
    responses={
        404: {"description": "데이터를 찾을 수 없습니다"},
        500: {"description": "서버 내부 오류"},
    }
)

# 서비스 인스턴스 생성
titanic_service = TitanicService()


@router.get(
    "/passengers/top10/simple",
    response_model=List[TitanicPassengerSimple],
    summary="상위 10명 승객 조회 (간단 버전)",
    description="""
    데이터셋에서 상위 10명의 승객 정보를 **간단하게** 반환합니다.
    
    ### 포함 정보
    - 승객 ID, 이름, 나이, 성별, 객실 등급, 생존 여부, 요금
    - 성별과 생존 여부는 한글로 표시됩니다
    
    ### Parameters
    - **dataset**: 조회할 데이터셋 선택
        - `train`: 학습 데이터셋 (891명, 생존 여부 포함)
        - `test`: 테스트 데이터셋 (418명, 생존 여부 미포함)
    
    ### Example Response
    ```json
    [
        {
            "PassengerId": 1,
            "Name": "Braund, Mr. Owen Harris",
            "Age": 22.0,
            "Sex": "남성",
            "Pclass": 3,
            "Survived": "사망",
            "Fare": 7.25
        }
    ]
    ```
    """,
    response_description="상위 10명의 승객 정보 (간단 버전)"
)
async def get_top_10_passengers_simple(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)", enum=["train", "test"])
):
    """상위 10명의 승객 정보를 간단하게 반환"""
    try:
        passengers = titanic_service.get_top_n_passengers_simple(n=10, dataset=dataset)
        return passengers
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get(
    "/passengers/top10",
    response_model=List[TitanicPassenger],
    summary="상위 10명 승객 조회 (전체 정보)",
    description="""
    데이터셋에서 상위 10명의 승객 정보를 **전체** 반환합니다.
    
    ### Parameters
    - **dataset**: 조회할 데이터셋 선택
        - `train`: 학습 데이터셋 (891명, 생존 여부 포함)
        - `test`: 테스트 데이터셋 (418명, 생존 여부 미포함)
    
    ### Returns
    - PassengerId부터 Embarked까지 모든 승객 정보를 포함한 리스트
    
    ### Example Response
    ```json
    [
        {
            "PassengerId": 1,
            "Survived": 0,
            "Pclass": 3,
            "Name": "Braund, Mr. Owen Harris",
            "Sex": "male",
            "Age": 22.0,
            "SibSp": 1,
            "Parch": 0,
            "Ticket": "A/5 21171",
            "Fare": 7.25,
            "Cabin": null,
            "Embarked": "S"
        }
    ]
    ```
    """,
    response_description="상위 10명의 승객 정보 리스트 (전체)"
)
async def get_top_10_passengers(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)", enum=["train", "test"])
):
    """상위 10명의 승객 정보를 반환 (전체)"""
    try:
        passengers = titanic_service.get_top_n_passengers(n=10, dataset=dataset)
        return passengers
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get("/passengers", response_model=List[TitanicPassenger])
async def get_all_passengers(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)"),
    limit: Optional[int] = Query(None, description="반환할 최대 승객 수")
):
    """
    모든 승객 정보를 반환
    
    Args:
        dataset: 데이터셋 선택 (train 또는 test)
        limit: 반환할 최대 승객 수
    
    Returns:
        List[TitanicPassenger]: 승객 정보 리스트
    """
    try:
        passengers = titanic_service.get_all_passengers(dataset=dataset)
        if limit:
            passengers = passengers[:limit]
        return passengers
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get("/passengers/{passenger_id}", response_model=TitanicPassenger)
async def get_passenger_by_id(
    passenger_id: int,
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    특정 승객 ID의 정보를 반환
    
    Args:
        passenger_id: 승객 ID
        dataset: 데이터셋 선택 (train 또는 test)
    
    Returns:
        TitanicPassenger: 승객 정보
    """
    try:
        passenger = titanic_service.get_passenger_by_id(passenger_id, dataset=dataset)
        if not passenger:
            raise HTTPException(status_code=404, detail=f"승객 ID {passenger_id}를 찾을 수 없습니다.")
        return passenger
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get("/passengers/filter/survived")
async def get_survived_passengers(
    survived: bool = Query(..., description="생존 여부 (True: 생존, False: 사망)"),
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    생존 여부로 승객을 필터링
    
    Args:
        survived: 생존 여부
        dataset: 데이터셋 선택 (train 또는 test)
    
    Returns:
        List[TitanicPassenger]: 필터링된 승객 정보
    """
    try:
        passengers = titanic_service.filter_by_survived(survived, dataset=dataset)
        return passengers
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get("/passengers/filter/class")
async def get_passengers_by_class(
    pclass: int = Query(..., description="객실 등급 (1, 2, 3)"),
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    객실 등급으로 승객을 필터링
    
    Args:
        pclass: 객실 등급
        dataset: 데이터셋 선택 (train 또는 test)
    
    Returns:
        List[TitanicPassenger]: 필터링된 승객 정보
    """
    try:
        passengers = titanic_service.filter_by_pclass(pclass, dataset=dataset)
        return passengers
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get("/passengers/filter/sex")
async def get_passengers_by_sex(
    sex: str = Query(..., description="성별 (male 또는 female)"),
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    성별로 승객을 필터링
    
    Args:
        sex: 성별
        dataset: 데이터셋 선택 (train 또는 test)
    
    Returns:
        List[TitanicPassenger]: 필터링된 승객 정보
    """
    try:
        passengers = titanic_service.filter_by_sex(sex, dataset=dataset)
        return passengers
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 오류: {str(e)}")


@router.get("/statistics/survival-rate")
async def get_survival_rate(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    생존율 통계를 반환
    
    Args:
        dataset: 데이터셋 선택 (train 또는 test)
    
    Returns:
        dict: 생존율 통계
    """
    try:
        stats = titanic_service.calculate_survival_rate(dataset=dataset)
        return stats
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 계산 오류: {str(e)}")


@router.get("/statistics/age")
async def get_age_statistics(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    나이 통계를 반환
    
    Args:
        dataset: 데이터셋 선택 (train 또는 test)
    
    Returns:
        dict: 나이 통계 (평균, 최소, 최대)
    """
    try:
        stats = titanic_service.calculate_age_statistics(dataset=dataset)
        return stats
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 계산 오류: {str(e)}")


# ========================================================================
# 데이터셋 분석 엔드포인트 (Pandas, NumPy, Scikit-learn, Datasets 활용)
# ========================================================================

@router.get("/dataset/summary", response_model=Dict[str, Any])
async def get_dataset_summary_api(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    데이터셋 요약 정보를 반환 (Pandas 활용)
    """
    try:
        summary = titanic_service.get_data_summary(dataset=dataset)
        return summary
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 요약 오류: {str(e)}")


@router.get("/dataset/correlation", response_model=Dict[str, Any])
async def get_correlation_matrix_api(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    숫자형 컬럼의 상관관계 매트릭스를 반환
    """
    try:
        correlation = titanic_service.calculate_correlation_matrix(dataset=dataset)
        return correlation
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상관관계 계산 오류: {str(e)}")


@router.get("/dataset/preprocess", response_model=Dict[str, Any])
async def preprocess_dataset_api(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    머신러닝을 위한 데이터 전처리 결과를 반환 (Scikit-learn 활용)
    """
    try:
        # preprocess() 메서드 사용 (TitanicMethod 활용)
        processed_data = titanic_service.preprocess()
        return processed_data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 전처리 오류: {str(e)}")


@router.post("/ml/modeling", response_model=Dict[str, Any])
async def modeling_api():
    """
    머신러닝 모델링 단계 실행
    """
    try:
        result = titanic_service.modeling()
        # 서비스에서 반환한 상태를 그대로 사용
        return {"status": result.get("status", "success"), "message": result.get("message", "모델링 완료"), "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델링 오류: {str(e)}")


@router.post("/ml/learning", response_model=Dict[str, Any])
async def learning_api():
    """
    머신러닝 학습 단계 실행
    """
    try:
        result = titanic_service.learning()
        # 서비스에서 반환한 상태를 그대로 사용
        return {"status": result.get("status", "success"), "message": result.get("message", "학습 완료"), "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"학습 오류: {str(e)}")


@router.post("/ml/evaluate", response_model=Dict[str, Any])
async def evaluate_api():
    """
    모델 평가 단계 실행 후 모델 평가 결과 반환
    """
    try:
        result = titanic_service.evaluate()
        # 서비스에서 반환한 상태를 그대로 사용
        return {"status": result.get("status", "success"), "message": result.get("message", "평가 완료"), "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"평가 오류: {str(e)}")


@router.post("/ml/submit", response_model=Dict[str, Any])
async def submit_api():
    """
    머신러닝 제출 단계 실행
    """
    try:
        result = titanic_service.submit()
        # 서비스에서 반환한 상태를 그대로 사용
        return {"status": result.get("status", "success"), "message": result.get("message", "제출 완료"), "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제출 오류: {str(e)}")


@router.get("/ml/submit/download")
async def download_submission():
    """
    캐글 제출용 submission.csv 파일 다운로드
    """
    try:
        # models 폴더 경로
        models_dir = Path(__file__).parent.parent / "models"
        submission_path = models_dir / "submission.csv"
        
        if not submission_path.exists():
            raise HTTPException(
                status_code=404, 
                detail="submission.csv 파일이 없습니다. 먼저 submit()을 실행해주세요."
            )
        
        return FileResponse(
            path=str(submission_path),
            filename="submission.csv",
            media_type="text/csv"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 오류: {str(e)}")


@router.get("/dataset/split", response_model=Dict[str, Any])
async def split_dataset_api(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)"),
    test_size: float = Query(0.2, description="테스트 데이터 비율 (0.0 ~ 1.0)"),
    random_state: int = Query(42, description="랜덤 시드")
):
    """
    학습/테스트 데이터 분할 정보를 반환 (Scikit-learn 활용)
    """
    try:
        split_info = titanic_service.split_train_test(
            dataset=dataset,
            test_size=test_size,
            random_state=random_state
        )
        return split_info
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 분할 오류: {str(e)}")


@router.get("/dataset/numpy-stats", response_model=Dict[str, Any])
async def get_numpy_statistics_api(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    NumPy를 활용한 통계 정보를 반환
    """
    try:
        stats = titanic_service.get_numpy_statistics(dataset=dataset)
        return stats
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 계산 오류: {str(e)}")


@router.get("/dataset/huggingface", response_model=Dict[str, Any])
async def get_huggingface_dataset(
    dataset: str = Query("train", description="데이터셋 선택 (train 또는 test)")
):
    """
    CSV 파일을 HuggingFace Dataset으로 로드하여 정보 반환
    """
    try:
        hf_dataset = titanic_service.load_huggingface_dataset(dataset=dataset)
        return {
            "dataset_name": dataset,
            "num_rows": hf_dataset.num_rows,
            "num_columns": hf_dataset.num_columns,
            "features": str(hf_dataset.features),
            "first_row": hf_dataset[0]
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HuggingFace Dataset 로드 오류: {str(e)}")


@router.get("/dataset/huggingface-dict", response_model=Dict[str, Any])
async def get_huggingface_dataset_dict():
    """
    train.csv와 test.csv를 로드하여 HuggingFace DatasetDict 정보 반환
    """
    try:
        dataset_dict = titanic_service.create_dataset_dict()
        return {
            "train_dataset_info": {
                "num_rows": dataset_dict["train"].num_rows,
                "num_columns": dataset_dict["train"].num_columns,
                "features": str(dataset_dict["train"].features),
                "first_row": dataset_dict["train"][0]
            },
            "test_dataset_info": {
                "num_rows": dataset_dict["test"].num_rows,
                "num_columns": dataset_dict["test"].num_columns,
                "features": str(dataset_dict["test"].features),
                "first_row": dataset_dict["test"][0]
            }
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HuggingFace DatasetDict 생성 오류: {str(e)}")
