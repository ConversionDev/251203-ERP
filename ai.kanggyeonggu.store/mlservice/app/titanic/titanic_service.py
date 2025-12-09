"""
Titanic Service - 비즈니스 로직
"""
from typing import Dict, Any, List, Optional

# 디버깅 도구 (icecream>=2.1.3)
from icecream import ic

# 내부 모듈
from app.titanic.titanic_method import TitanicMethod
from app.titanic.titanic_model import TitanicPassenger, TitanicPassengerList, TitanicPassengerSimple
from app.titanic.titanic_dataset import TitanicDataset

# TODO: 향후 사용 예정 (다른 메서드에서 사용)
import pandas as pd  # pandas>=2.1.0
import numpy as np  # numpy>=1.24.0
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
# from sklearn.preprocessing import StandardScaler, OneHotEncoder
# from sklearn.compose import ColumnTransformer
# from sklearn.impute import SimpleImputer
# from sklearn.pipeline import Pipeline
# from datasets import Dataset, DatasetDict


class TitanicService:
    """타이타닉 데이터 서비스"""
    
    def __init__(self):
        """초기화"""
        # 기존 데이터 조회 메서드를 위한 초기화
        self.train_csv_path = Path(__file__).parent / "train.csv"
        self.test_csv_path = Path(__file__).parent / "test.csv"
        self.train_df: Optional[pd.DataFrame] = None
        self.test_df: Optional[pd.DataFrame] = None
        
        # 전처리된 데이터 및 모델 저장
        self.processed_dataset: Optional[TitanicDataset] = None
        self.train_labels: Optional[pd.DataFrame] = None
        self.models: Dict[str, Any] = {}
        self.X_train: Optional[pd.DataFrame] = None
        self.X_test: Optional[pd.DataFrame] = None
        self.y_train: Optional[pd.Series] = None
        self.y_test: Optional[pd.Series] = None
        
        ic(f"📁 Train CSV 경로: {self.train_csv_path}")
        ic(f"📁 Test CSV 경로: {self.test_csv_path}")
    
    def load_data(self, dataset: str = "train") -> pd.DataFrame:
        """CSV 데이터 로드"""
        if dataset == "train":
            if self.train_df is None:
                ic("📂 학습 데이터 로딩 중...")
                if not self.train_csv_path.exists():
                    raise FileNotFoundError(f"Train CSV 파일을 찾을 수 없습니다: {self.train_csv_path}")
                self.train_df = pd.read_csv(self.train_csv_path)
                ic(f"✅ {len(self.train_df)}개 승객 데이터 로드 완료")
            return self.train_df
        else:  # test
            if self.test_df is None:
                ic("📂 테스트 데이터 로딩 중...")
                if not self.test_csv_path.exists():
                    raise FileNotFoundError(f"Test CSV 파일을 찾을 수 없습니다: {self.test_csv_path}")
                self.test_df = pd.read_csv(self.test_csv_path)
                ic(f"✅ {len(self.test_df)}개 승객 데이터 로드 완료")
            return self.test_df
    
    def get_top_n_passengers_simple(self, n: int = 10, dataset: str = "train") -> List[TitanicPassengerSimple]:
        """상위 N명 승객 조회 (간단 버전)"""
        try:
            df = self.load_data(dataset)
            if df is None or df.empty:
                raise ValueError(f"{dataset} 데이터셋이 비어있습니다.")
            
            top_df = df.head(n)
            
            passengers = []
            for _, row in top_df.iterrows():
                # 성별 한글 변환
                sex_value = row.get('Sex', '')
                sex_kr = "남성" if sex_value == "male" else "여성" if sex_value == "female" else "미상"
                
                # 생존 여부 한글 변환 (train 데이터셋만)
                if 'Survived' in row and pd.notna(row['Survived']):
                    survived_kr = "생존" if int(row['Survived']) == 1 else "사망"
                else:
                    survived_kr = "미확인"  # test 데이터셋
                
                passenger = TitanicPassengerSimple(
                    PassengerId=int(row.get('PassengerId', 0)),
                    Name=str(row.get('Name', '')),
                    Age=float(row['Age']) if pd.notna(row.get('Age')) else None,
                    Sex=sex_kr,
                    Pclass=int(row.get('Pclass', 0)),
                    Survived=survived_kr,
                    Fare=float(row['Fare']) if pd.notna(row.get('Fare')) else None
                )
                passengers.append(passenger)
            
            ic(f"📋 상위 {n}명 승객 조회 완료")
            return passengers
        except Exception as e:
            ic(f"❌ 승객 데이터 조회 오류: {str(e)}")
            raise
    
    def get_top_n_passengers(self, n: int = 10, dataset: str = "train") -> List[TitanicPassenger]:
        """상위 N명 승객 조회 (전체 정보)"""
        df = self.load_data(dataset)
        top_df = df.head(n)
        
        passengers = []
        for _, row in top_df.iterrows():
            passenger = TitanicPassenger(
                PassengerId=int(row['PassengerId']),
                Survived=int(row['Survived']) if 'Survived' in row and pd.notna(row['Survived']) else None,
                Pclass=int(row['Pclass']),
                Name=row['Name'],
                Sex=row['Sex'],
                Age=float(row['Age']) if pd.notna(row['Age']) else None,
                SibSp=int(row['SibSp']),
                Parch=int(row['Parch']),
                Ticket=row['Ticket'],
                Fare=float(row['Fare']) if pd.notna(row['Fare']) else None,
                Cabin=row['Cabin'] if pd.notna(row['Cabin']) else None,
                Embarked=row['Embarked'] if pd.notna(row['Embarked']) else None
            )
            passengers.append(passenger)
        
        ic(f"📋 상위 {n}명 승객 조회 완료 (전체 정보)")
        return passengers
    
    def get_all_passengers(self, dataset: str = "train") -> List[TitanicPassenger]:
        """전체 승객 조회"""
        df = self.load_data(dataset)
        
        passengers = []
        for _, row in df.iterrows():
            passenger = TitanicPassenger(
                PassengerId=int(row['PassengerId']),
                Survived=int(row['Survived']) if 'Survived' in row and pd.notna(row['Survived']) else None,
                Pclass=int(row['Pclass']),
                Name=row['Name'],
                Sex=row['Sex'],
                Age=float(row['Age']) if pd.notna(row['Age']) else None,
                SibSp=int(row['SibSp']),
                Parch=int(row['Parch']),
                Ticket=row['Ticket'],
                Fare=float(row['Fare']) if pd.notna(row['Fare']) else None,
                Cabin=row['Cabin'] if pd.notna(row['Cabin']) else None,
                Embarked=row['Embarked'] if pd.notna(row['Embarked']) else None
            )
            passengers.append(passenger)
        
        ic(f"📋 전체 {len(passengers)}명 승객 조회 완료")
        return passengers
    
    def get_passenger_by_id(self, passenger_id: int, dataset: str = "train") -> Optional[TitanicPassenger]:
        """승객 ID로 조회"""
        df = self.load_data(dataset)
        passenger_df = df[df['PassengerId'] == passenger_id]
        
        if passenger_df.empty:
            ic(f"❌ 승객 {passenger_id} 없음")
            return None
        
        row = passenger_df.iloc[0]
        passenger = TitanicPassenger(
            PassengerId=int(row['PassengerId']),
            Survived=int(row['Survived']) if 'Survived' in row and pd.notna(row['Survived']) else None,
            Pclass=int(row['Pclass']),
            Name=row['Name'],
            Sex=row['Sex'],
            Age=float(row['Age']) if pd.notna(row['Age']) else None,
            SibSp=int(row['SibSp']),
            Parch=int(row['Parch']),
            Ticket=row['Ticket'],
            Fare=float(row['Fare']) if pd.notna(row['Fare']) else None,
            Cabin=row['Cabin'] if pd.notna(row['Cabin']) else None,
            Embarked=row['Embarked'] if pd.notna(row['Embarked']) else None
        )
        
        ic(f"✅ 승객 {passenger_id} 조회 완료")
        return passenger
    
    #전처리 단계
    def preprocess(self) -> Dict[str, Any]:
        """
        타이타닉 데이터 전처리 실행
        
        Returns:
            전처리 결과 정보 딕셔너리
        """
        logs = []
        logs.append("😎😎 전처리 시작")
        ic("😎😎 전처리 시작")
        
        the_method = TitanicMethod()
        
        # CSV 파일 읽기
        df_train = the_method.read_csv("train.csv")
        df_test = the_method.read_csv("test.csv")
        
        # Survived label 저장
        self.train_labels = the_method.create_label(df_train, "Survived")
        
        # Survived 컬럼 제거
        train_df = the_method.create_df(df_train, "Survived")
        test_df = the_method.create_df(df_test, "Survived")
        
        # 전처리 전 데이터 저장
        before_train = train_df.copy()
        before_columns = before_train.columns.tolist()
        before_sample_data = before_train.head(5).to_dict(orient="records")
        
        # TitanicDataset 객체 생성
        this = TitanicDataset(train=train_df.copy(), test=test_df.copy())
        before_null_count = the_method.check_null(this)
        
        logs.append(f"1. Train 의 type: {type(this.train)}")
        logs.append(f"2. Train 의 column: {list(this.train.columns)}")
        logs.append(f"3. Train 의 상위 5개 행:\n{this.train.head(5).to_string()}")
        logs.append(f"4. Train 의 null 의 갯수: {the_method.check_null(TitanicDataset(train=this.train))}개")
        
        logs.append(f"1. Test 의 type: {type(this.test)}")
        logs.append(f"2. Test 의 column: {list(this.test.columns)}")
        logs.append(f"3. Test 의 상위 5개 행:\n{this.test.head(5).to_string()}")
        logs.append(f"4. Test 의 null 의 갯수: {the_method.check_null(TitanicDataset(test=this.test))}개")
        
        ic(f"1. Train 의 type \n {type(this.train)}")
        ic(f"2. Train 의 column \n {list(this.train.columns)}")
        ic(f"3. Train 의 상위 5개 행\n {this.train.head(5)}")
        ic(f"4. Train 의 null 의 갯수\n {the_method.check_null(TitanicDataset(train=this.train))}개")
        
        ic(f"1. Test 의 type \n {type(this.test)}")
        ic(f"2. Test 의 column \n {list(this.test.columns)}")
        ic(f"3. Test 의 상위 5개 행\n {this.test.head(5)}")
        ic(f"4. Test 의 null 의 갯수\n {the_method.check_null(TitanicDataset(test=this.test))}개")
        
        # 전처리 실행
        drop_features = ['SibSp', 'Parch', 'Cabin', 'Ticket']
        this = the_method.drop_feature(this, *drop_features)
        this = the_method.pclass_ordinal(this)
        this = the_method.fare_ordinal(this)
        this = the_method.embarked_ordinal(this)
        this = the_method.gender_nominal(this)
        this = the_method.age_ratio(this)
        this = the_method.title_nominal(this)
        drop_name = ['Name']
        this = the_method.drop_feature(this, *drop_name)
        
        logs.append("😎😎 전처리 완료")
        logs.append(f"1. Train 의 type: {type(this.train)}")
        logs.append(f"2. Train 의 column: {list(this.train.columns)}")
        logs.append(f"3. Train 의 상위 5개 행:\n{this.train.head(5).to_string()}")
        logs.append(f"4. Train 의 null 의 갯수: {the_method.check_null(TitanicDataset(train=this.train))}개")
        
        logs.append(f"1. Test 의 type: {type(this.test)}")
        logs.append(f"2. Test 의 column: {list(this.test.columns)}")
        logs.append(f"3. Test 의 상위 5개 행:\n{this.test.head(5).to_string()}")
        logs.append(f"4. Test 의 null 의 갯수: {the_method.check_null(TitanicDataset(test=this.test))}개")
        
        ic("😎😎 전처리 완료")
        ic(f"1. Train 의 type \n {type(this.train)}")
        ic(f"2. Train 의 column \n {list(this.train.columns)}")
        ic(f"3. Train 의 상위 5개 행\n {this.train.head(5)}")
        ic(f"4. Train 의 null 의 갯수\n {the_method.check_null(TitanicDataset(train=this.train))}개")
        
        ic(f"1. Test 의 type \n {type(this.test)}")
        ic(f"2. Test 의 column \n {list(this.test.columns)}")
        ic(f"3. Test 의 상위 5개 행\n {this.test.head(5)}")
        ic(f"4. Test 의 null 의 갯수\n {the_method.check_null(TitanicDataset(test=this.test))}개")
        
        # 전처리 결과 정보 반환 (프론트엔드가 logs 배열을 기대함)
        # 터미널 로그와 동일하게 모든 값을 정수로 변환하여 반환
        sample_df_train = this.train.head(5).copy()
        for col in sample_df_train.columns:
            if pd.api.types.is_numeric_dtype(sample_df_train[col]):
                sample_df_train[col] = sample_df_train[col].fillna(0).astype(int)
        
        sample_df_test = this.test.head(5).copy()
        for col in sample_df_test.columns:
            if pd.api.types.is_numeric_dtype(sample_df_test[col]):
                sample_df_test[col] = sample_df_test[col].fillna(0).astype(int)
        
        sample_data_train = sample_df_train.to_dict(orient="records")
        sample_data_test = sample_df_test.to_dict(orient="records")
        
        # 전처리된 데이터 저장 (모델링/학습/평가에서 사용)
        self.processed_dataset = this
        
        return {
            "logs": logs,
            "status": "success",
            "train": {
                "rows": len(this.train),
                "columns": this.train.columns.tolist(),
                "column_count": len(this.train.columns),
                "null_count": int(the_method.check_null(TitanicDataset(train=this.train))),
                "sample_data": sample_data_train
            },
            "test": {
                "rows": len(this.test),
                "columns": this.test.columns.tolist(),
                "column_count": len(this.test.columns),
                "null_count": int(the_method.check_null(TitanicDataset(test=this.test))),
                "sample_data": sample_data_test
            },
            "before": {
                "columns": before_columns,
                "column_count": len(before_columns),
                "null_count": before_null_count,
                "sample_data": before_sample_data
            }
        }

    def modeling(self) -> Dict[str, Any]:
        """모델링 단계 - 여러 알고리즘 모델 초기화"""
        logs = []
        logs.append("😎😎 모델링 시작")
        ic("😎😎 모델링 시작")
        
        if self.processed_dataset is None or self.train_labels is None:
            logs.append("❌ 오류: 전처리가 먼저 실행되어야 합니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "전처리가 먼저 실행되어야 합니다. preprocess()를 먼저 호출하세요."
            }
        
        # 모델 초기화 (가장 성능이 좋은 랜덤 포레스트만 사용)
        self.models = {
            "랜덤 포레스트": RandomForestClassifier(random_state=42, n_estimators=100)
        }
        
        logs.append(f"✅ {len(self.models)}개 모델 초기화 완료")
        logs.append(f"초기화된 모델: 랜덤 포레스트 (최고 성능 모델)")
        
        # 모델별 상세 정보
        model_info = []
        for model_name, model in self.models.items():
            model_params = {}
            if hasattr(model, 'get_params'):
                params = model.get_params()
                # 주요 파라미터만 선택
                key_params = {k: v for k, v in params.items() if k in ['random_state', 'n_estimators']}
                model_params = key_params
            model_info.append({
                "name": model_name,
                "type": type(model).__name__,
                "parameters": model_params
            })
            logs.append(f"  - {model_name} ({type(model).__name__}): {model_params}")
        
        logs.append("😎😎 모델링 완료")
        ic(f"✅ {len(self.models)}개 모델 초기화 완료: {list(self.models.keys())}")
        ic("😎😎 모델링 완료")
        
        
        return {
            "logs": logs,
            "status": "success",
            "message": f"{len(self.models)}개 모델이 초기화되었습니다.",
            "models": list(self.models.keys()),
            "model_count": len(self.models),
            "model_info": model_info
        }

    def learning(self) -> Dict[str, Any]:
        """학습 단계 - 전처리된 데이터로 모델 학습"""
        logs = []
        logs.append("😎😎 학습 시작")
        ic("😎😎 학습 시작")
        
        if self.processed_dataset is None or self.train_labels is None:
            logs.append("❌ 오류: 전처리가 먼저 실행되어야 합니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "전처리가 먼저 실행되어야 합니다. preprocess()를 먼저 호출하세요."
            }
        
        if not self.models:
            logs.append("❌ 오류: 모델이 초기화되지 않았습니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "모델이 초기화되지 않았습니다. modeling()을 먼저 호출하세요."
            }
        
        # 전처리된 데이터 준비
        X = self.processed_dataset.train
        y = self.train_labels["Survived"]
        
        logs.append(f"전처리된 데이터 준비 완료")
        logs.append(f"  - 입력 데이터(X) 크기: {X.shape}")
        logs.append(f"  - 타겟 데이터(y) 크기: {y.shape}")
        
        # 학습/검증 데이터 분할
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logs.append(f"학습/검증 데이터 분할 완료")
        logs.append(f"  - 학습 데이터: {len(self.X_train)}개 ({len(self.X_train)/len(X)*100:.1f}%)")
        logs.append(f"  - 검증 데이터: {len(self.X_test)}개 ({len(self.X_test)/len(X)*100:.1f}%)")
        ic(f"학습 데이터: {len(self.X_train)}개, 검증 데이터: {len(self.X_test)}개")
        
        # 모델 학습 (랜덤 포레스트)
        trained_models = {}
        logs.append("모델 학습 시작:")
        for model_name, model in self.models.items():
            logs.append(f"  {model_name} 학습 중...")
            ic(f"📚 {model_name} 학습 중...")
            model.fit(self.X_train, self.y_train)
            trained_models[model_name] = "학습 완료"
            logs.append(f"     ✅ {model_name} 학습 완료")
            ic(f"✅ {model_name} 학습 완료")
        
        logs.append("😎😎 학습 완료")
        logs.append(f"랜덤 포레스트 모델 학습 완료")
        ic("😎😎 학습 완료")
        
        return {
            "logs": logs,
            "status": "success",
            "message": f"{len(trained_models)}개 모델 학습 완료",
            "trained_models": list(trained_models.keys()),
            "train_size": len(self.X_train),
            "test_size": len(self.X_test),
            "model_count": len(trained_models)
        }
    
    #후처리 단계(추론 단계) 
    def evaluate(self) -> Dict[str, Any]:
        """평가 단계 - 학습된 모델들의 검증 정확도 평가"""
        logs = []
        logs.append("😎😎 평가 시작")
        ic("😎😎 평가 시작")
        
        if not self.models:
            logs.append("❌ 오류: 모델이 초기화되지 않았습니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "모델이 초기화되지 않았습니다. modeling()을 먼저 호출하세요."
            }
        
        if self.X_test is None or self.y_test is None:
            logs.append("❌ 오류: 학습이 먼저 실행되어야 합니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "학습이 먼저 실행되어야 합니다. learning()을 먼저 호출하세요."
            }
        
        logs.append(f"검증 데이터 준비 완료")
        logs.append(f"  - 검증 데이터 크기: {len(self.X_test)}개")
        logs.append("모델 평가 시작:")
        
        # 랜덤 포레스트 모델 평가
        results = {}
        for model_name, model in self.models.items():
            logs.append(f"  {model_name} 평가 중...")
            y_pred = model.predict(self.X_test)
            accuracy = accuracy_score(self.y_test, y_pred)
            results[model_name] = round(accuracy * 100, 2)
            logs.append(f"     ✅ {model_name} 활용한 검증 정확도: {accuracy * 100:.2f}%")
            ic(f'{model_name} 활용한 검증 정확도: {accuracy * 100:.2f}%')
        
        # 최고 성능 모델 (랜덤 포레스트)
        best_model = list(results.keys())[0] if results else None
        best_accuracy = list(results.values())[0] if results else None
        
        logs.append("😎😎 평가 완료")
        logs.append("=" * 50)
        logs.append("평가 결과:")
        if best_model and best_accuracy:
            logs.append(f"  - 모델: {best_model}")
            logs.append(f"  - 검증 정확도: {best_accuracy}%")
        logs.append("=" * 50)
        
        ic("😎😎 평가 완료")
        
        return {
            "logs": logs,
            "status": "success",
            "message": "모델 평가 완료",
            "results": results,
            "best_model": best_model,
            "best_accuracy": best_accuracy,
            "model_count": len(results)
        }

    def submit(self) -> Dict[str, Any]:
        """제출 단계 - 캐글 제출용 submission.csv 파일 생성"""
        logs = []
        logs.append("😎😎 제출 시작")
        ic("😎😎 제출 시작")
        
        if not self.models:
            logs.append("❌ 오류: 모델이 초기화되지 않았습니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "모델이 초기화되지 않았습니다. modeling()을 먼저 호출하세요."
            }
        
        if self.processed_dataset is None:
            logs.append("❌ 오류: 전처리가 먼저 실행되어야 합니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "전처리가 먼저 실행되어야 합니다. preprocess()를 먼저 호출하세요."
            }
        
        # 학습된 모델 확인
        if not hasattr(list(self.models.values())[0], 'predict'):
            logs.append("❌ 오류: 모델이 학습되지 않았습니다.")
            return {
                "logs": logs,
                "status": "error",
                "message": "모델이 학습되지 않았습니다. learning()을 먼저 호출하세요."
            }
        
        # test.csv 데이터에 대한 예측 수행
        X_test_submit = self.processed_dataset.test
        model = list(self.models.values())[0]  # 랜덤 포레스트 모델
        
        logs.append("테스트 데이터 예측 시작...")
        ic("테스트 데이터 예측 시작...")
        
        # 예측 수행
        predictions = model.predict(X_test_submit)
        
        # PassengerId 가져오기
        the_method = TitanicMethod()
        df_test_original = the_method.read_csv("test.csv")
        passenger_ids = df_test_original["PassengerId"].values
        
        logs.append(f"예측 완료: {len(predictions)}개")
        logs.append(f"PassengerId 범위: {passenger_ids.min()} ~ {passenger_ids.max()}")
        
        # submission.csv 생성
        submission_df = pd.DataFrame({
            'PassengerId': passenger_ids,
            'Survived': predictions.astype(int)
        })
        
        # models 폴더에 저장
        # __file__은 titanic_service.py의 경로이므로, parent.parent는 app/ 디렉토리
        models_dir = Path(__file__).parent.parent / "models"
        models_dir.mkdir(exist_ok=True, parents=True)
        submission_path = models_dir / "submission.csv"
        
        # 절대 경로로 변환하여 로그에 표시
        abs_submission_path = submission_path.resolve()
        
        logs.append(f"저장 경로: {abs_submission_path}")
        logs.append(f"디렉토리 생성 확인: {models_dir.exists()}")
        logs.append(f"디렉토리 절대 경로: {models_dir.resolve()}")
        
        # CSV 파일 저장
        try:
            submission_df.to_csv(submission_path, index=False)
            logs.append(f"파일 저장 시도 완료")
        except Exception as e:
            logs.append(f"파일 저장 오류: {str(e)}")
            raise
        
        # 파일 생성 확인
        if submission_path.exists():
            file_size = submission_path.stat().st_size
            logs.append(f"✅ 제출 파일 생성 완료: {abs_submission_path}")
            logs.append(f"파일 크기: {file_size} bytes")
            logs.append(f"총 예측 수: {len(submission_df)}개")
            logs.append(f"생존 예측: {predictions.sum()}명 ({predictions.sum()/len(predictions)*100:.2f}%)")
            logs.append(f"사망 예측: {(predictions == 0).sum()}명 ({(predictions == 0).sum()/len(predictions)*100:.2f}%)")
            logs.append("😎😎 제출 완료")
            
            ic(f"✅ 제출 파일 생성 완료: {abs_submission_path}")
            ic(f"파일 크기: {file_size} bytes")
            ic("😎😎 제출 완료")
        else:
            logs.append(f"❌ 오류: 파일 생성 실패 - {abs_submission_path}")
            ic(f"❌ 오류: 파일 생성 실패 - {abs_submission_path}")
        
        return {
            "logs": logs,
            "status": "success" if submission_path.exists() else "error",
            "message": "캐글 제출 파일이 생성되었습니다." if submission_path.exists() else "파일 생성에 실패했습니다.",
            "file_path": str(abs_submission_path),
            "file_name": "submission.csv",
            "file_exists": submission_path.exists(),
            "total_predictions": len(submission_df),
            "survived_count": int(predictions.sum()),
            "died_count": int((predictions == 0).sum()),
            "sample_predictions": submission_df.head(10).to_dict(orient="records")
        }
    
    # ========================================================================
    # Router에서 호출하는 추가 메서드들 (향후 구현 예정)
    # ========================================================================
    
    def filter_by_survived(self, survived: bool, dataset: str = "train") -> List[TitanicPassenger]:
        """생존 여부로 필터링"""
        df = self.load_data(dataset)
        if 'Survived' not in df.columns:
            return []
        filtered_df = df[df['Survived'] == (1 if survived else 0)]
        
        passengers = []
        for _, row in filtered_df.iterrows():
            passenger = TitanicPassenger(
                PassengerId=int(row['PassengerId']),
                Survived=int(row['Survived']) if pd.notna(row['Survived']) else None,
                Pclass=int(row['Pclass']),
                Name=row['Name'],
                Sex=row['Sex'],
                Age=float(row['Age']) if pd.notna(row['Age']) else None,
                SibSp=int(row['SibSp']),
                Parch=int(row['Parch']),
                Ticket=row['Ticket'],
                Fare=float(row['Fare']) if pd.notna(row['Fare']) else None,
                Cabin=row['Cabin'] if pd.notna(row['Cabin']) else None,
                Embarked=row['Embarked'] if pd.notna(row['Embarked']) else None
            )
            passengers.append(passenger)
        return passengers
    
    def filter_by_pclass(self, pclass: int, dataset: str = "train") -> List[TitanicPassenger]:
        """객실 등급으로 필터링"""
        df = self.load_data(dataset)
        filtered_df = df[df['Pclass'] == pclass]
        
        passengers = []
        for _, row in filtered_df.iterrows():
            passenger = TitanicPassenger(
                PassengerId=int(row['PassengerId']),
                Survived=int(row['Survived']) if 'Survived' in row and pd.notna(row['Survived']) else None,
                Pclass=int(row['Pclass']),
                Name=row['Name'],
                Sex=row['Sex'],
                Age=float(row['Age']) if pd.notna(row['Age']) else None,
                SibSp=int(row['SibSp']),
                Parch=int(row['Parch']),
                Ticket=row['Ticket'],
                Fare=float(row['Fare']) if pd.notna(row['Fare']) else None,
                Cabin=row['Cabin'] if pd.notna(row['Cabin']) else None,
                Embarked=row['Embarked'] if pd.notna(row['Embarked']) else None
            )
            passengers.append(passenger)
        return passengers
    
    def filter_by_sex(self, sex: str, dataset: str = "train") -> List[TitanicPassenger]:
        """성별로 필터링"""
        df = self.load_data(dataset)
        filtered_df = df[df['Sex'] == sex]
        
        passengers = []
        for _, row in filtered_df.iterrows():
            passenger = TitanicPassenger(
                PassengerId=int(row['PassengerId']),
                Survived=int(row['Survived']) if 'Survived' in row and pd.notna(row['Survived']) else None,
                Pclass=int(row['Pclass']),
                Name=row['Name'],
                Sex=row['Sex'],
                Age=float(row['Age']) if pd.notna(row['Age']) else None,
                SibSp=int(row['SibSp']),
                Parch=int(row['Parch']),
                Ticket=row['Ticket'],
                Fare=float(row['Fare']) if pd.notna(row['Fare']) else None,
                Cabin=row['Cabin'] if pd.notna(row['Cabin']) else None,
                Embarked=row['Embarked'] if pd.notna(row['Embarked']) else None
            )
            passengers.append(passenger)
        return passengers
    
    def calculate_survival_rate(self, dataset: str = "train") -> Dict[str, Any]:
        """생존율 통계 계산"""
        df = self.load_data(dataset)
        if 'Survived' not in df.columns:
            return {"error": "Survived 컬럼이 없습니다"}
        
        total = len(df)
        survived = df['Survived'].sum()
        died = total - survived
        survival_rate = (survived / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "survived": int(survived),
            "died": int(died),
            "survival_rate": round(survival_rate, 2)
        }
    
    def calculate_age_statistics(self, dataset: str = "train") -> Dict[str, Any]:
        """나이 통계 계산"""
        df = self.load_data(dataset)
        age_series = df['Age'].dropna()
        
        if len(age_series) == 0:
            return {"error": "나이 데이터가 없습니다"}
        
        return {
            "mean": round(float(age_series.mean()), 2),
            "min": round(float(age_series.min()), 2),
            "max": round(float(age_series.max()), 2),
            "median": round(float(age_series.median()), 2),
            "std": round(float(age_series.std()), 2)
        }
    
    def get_data_summary(self, dataset: str = "train") -> Dict[str, Any]:
        """데이터셋 요약 정보"""
        df = self.load_data(dataset)
        return {
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict(),
            "describe": df.describe().to_dict()
        }
    
    def calculate_correlation_matrix(self, dataset: str = "train") -> Dict[str, Any]:
        """상관관계 매트릭스 계산"""
        df = self.load_data(dataset)
        numeric_df = df.select_dtypes(include=[np.number])
        correlation = numeric_df.corr()
        return {
            "correlation_matrix": correlation.to_dict(),
            "columns": list(correlation.columns)
        }
    
    def preprocess_data_for_ml(self, dataset: str = "train") -> Dict[str, Any]:
        """ML을 위한 데이터 전처리"""
        # TODO: 향후 구현
        return {"message": "전처리 기능은 향후 구현 예정입니다"}
    
    def split_train_test(self, dataset: str = "train", test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
        """학습/테스트 데이터 분할"""
        # TODO: 향후 구현
        return {"message": "데이터 분할 기능은 향후 구현 예정입니다"}
    
    def get_numpy_statistics(self, dataset: str = "train") -> Dict[str, Any]:
        """NumPy를 활용한 통계 정보"""
        df = self.load_data(dataset)
        numeric_df = df.select_dtypes(include=[np.number])
        
        return {
            "mean": {col: float(np.mean(numeric_df[col].dropna())) for col in numeric_df.columns},
            "std": {col: float(np.std(numeric_df[col].dropna())) for col in numeric_df.columns},
            "min": {col: float(np.min(numeric_df[col].dropna())) for col in numeric_df.columns},
            "max": {col: float(np.max(numeric_df[col].dropna())) for col in numeric_df.columns}
        }
    
    def load_huggingface_dataset(self, dataset: str = "train") -> Any:
        """HuggingFace Dataset으로 로드"""
        # TODO: 향후 구현
        from datasets import Dataset
        df = self.load_data(dataset)
        return Dataset.from_pandas(df)
    
    def create_dataset_dict(self) -> Any:
        """HuggingFace DatasetDict 생성"""
        # TODO: 향후 구현
        from datasets import Dataset, DatasetDict
        train_df = self.load_data("train")
        test_df = self.load_data("test")
        
        return DatasetDict({
            "train": Dataset.from_pandas(train_df),
            "test": Dataset.from_pandas(test_df)
        })