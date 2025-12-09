"""
Customer Service - 비즈니스 로직
B2B ERP 고객 데이터 분석 및 ML 서비스
"""
import csv
from pathlib import Path
from typing import List, Optional, Dict, Any

# 데이터 분석 및 머신러닝 라이브러리
import pandas as pd
import numpy as np

# Scikit-learn 모듈들
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# HuggingFace Datasets
from datasets import Dataset, DatasetDict

# 디버깅 도구
from icecream import ic

# 내부 모듈
from app.customer.customer_model import (
    CustomerDetail, CustomerSimple, CustomerStatistics,
    IndustryStatistics, ChurnPrediction, CustomerModel
)


class CustomerService:
    """고객 데이터 서비스"""
    
    def __init__(self):
        """초기화"""
        self.csv_path = Path(__file__).parent / "customer_data.csv"
        self.df: Optional[pd.DataFrame] = None
        self.model = CustomerModel()
        ic(f"📁 CSV 경로: {self.csv_path}")
    
    def load_data(self) -> pd.DataFrame:
        """CSV 데이터 로드"""
        if self.df is None:
            ic("📂 고객 데이터 로딩 중...")
            self.df = pd.read_csv(self.csv_path)
            ic(f"✅ {len(self.df)}개 고객 데이터 로드 완료")
        return self.df
    
    # ========================================================================
    # 1. 고객 데이터 조회 (CRUD)
    # ========================================================================
    
    def get_all_customers(self, limit: Optional[int] = None) -> List[CustomerDetail]:
        """전체 고객 조회"""
        df = self.load_data()
        
        if limit:
            df = df.head(limit)
        
        customers = []
        for _, row in df.iterrows():
            customer = CustomerDetail(**row.to_dict())
            customers.append(customer)
        
        ic(f"📋 {len(customers)}개 고객 조회")
        return customers
    
    def get_customers_simple(self, limit: Optional[int] = None) -> List[CustomerSimple]:
        """고객 간단 정보 조회 (화면 표시용)"""
        df = self.load_data()
        
        if limit:
            df = df.head(limit)
        
        customers = []
        for _, row in df.iterrows():
            customer = CustomerSimple(
                customer_id=row['customer_id'],
                company_name=row['company_name'],
                status=row['status'],
                total_orders=row['total_orders'],
                total_revenue=row['total_revenue'],
                churn_risk="위험" if row['churn_risk'] == 1 else "안전"
            )
            customers.append(customer)
        
        return customers
    
    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerDetail]:
        """고객 ID로 조회"""
        df = self.load_data()
        customer_df = df[df['customer_id'] == customer_id]
        
        if customer_df.empty:
            ic(f"❌ 고객 {customer_id} 없음")
            return None
        
        customer = CustomerDetail(**customer_df.iloc[0].to_dict())
        ic(f"✅ 고객 {customer_id} 조회 완료")
        return customer
    
    def filter_by_status(self, status: str) -> List[CustomerDetail]:
        """상태별 필터링 (활성/비활성)"""
        df = self.load_data()
        filtered_df = df[df['status'] == status]
        
        customers = []
        for _, row in filtered_df.iterrows():
            customers.append(CustomerDetail(**row.to_dict()))
        
        ic(f"📊 상태={status}: {len(customers)}개")
        return customers
    
    def filter_by_industry(self, industry: str) -> List[CustomerDetail]:
        """업종별 필터링"""
        df = self.load_data()
        filtered_df = df[df['industry'] == industry]
        
        customers = []
        for _, row in filtered_df.iterrows():
            customers.append(CustomerDetail(**row.to_dict()))
        
        ic(f"📊 업종={industry}: {len(customers)}개")
        return customers
    
    def filter_by_churn_risk(self, risk: int) -> List[CustomerDetail]:
        """이탈 위험도별 필터링 (0=안전, 1=위험)"""
        df = self.load_data()
        filtered_df = df[df['churn_risk'] == risk]
        
        customers = []
        for _, row in filtered_df.iterrows():
            customers.append(CustomerDetail(**row.to_dict()))
        
        risk_label = "위험" if risk == 1 else "안전"
        ic(f"📊 이탈 위험={risk_label}: {len(customers)}개")
        return customers
    
    # ========================================================================
    # 2. 통계 분석
    # ========================================================================
    
    def get_statistics(self) -> CustomerStatistics:
        """전체 고객 통계"""
        df = self.load_data()
        
        stats = CustomerStatistics(
            total_customers=len(df),
            active_customers=len(df[df['status'] == '활성']),
            inactive_customers=len(df[df['status'] == '비활성']),
            high_risk_customers=len(df[df['churn_risk'] == 1]),
            total_revenue=int(df['total_revenue'].sum()),
            avg_revenue_per_customer=float(df['total_revenue'].mean()),
            avg_orders_per_customer=float(df['total_orders'].mean())
        )
        
        ic("📊 통계 계산 완료")
        return stats
    
    def get_industry_statistics(self) -> List[IndustryStatistics]:
        """업종별 통계"""
        df = self.load_data()
        
        industry_stats = []
        for industry in df['industry'].unique():
            industry_df = df[df['industry'] == industry]
            
            stat = IndustryStatistics(
                industry=industry,
                customer_count=len(industry_df),
                total_revenue=int(industry_df['total_revenue'].sum()),
                avg_revenue=float(industry_df['total_revenue'].mean()),
                churn_rate=float(industry_df['churn_risk'].mean() * 100)
            )
            industry_stats.append(stat)
        
        # 매출 순으로 정렬
        industry_stats.sort(key=lambda x: x.total_revenue, reverse=True)
        
        ic(f"📊 {len(industry_stats)}개 업종 통계 완료")
        return industry_stats
    
    def get_top_customers(self, limit: int = 10, by: str = "revenue") -> List[CustomerDetail]:
        """상위 고객 조회"""
        df = self.load_data()
        
        if by == "revenue":
            sorted_df = df.sort_values('total_revenue', ascending=False)
        elif by == "orders":
            sorted_df = df.sort_values('total_orders', ascending=False)
        else:
            sorted_df = df
        
        top_df = sorted_df.head(limit)
        
        customers = []
        for _, row in top_df.iterrows():
            customers.append(CustomerDetail(**row.to_dict()))
        
        ic(f"🏆 상위 {limit}개 고객 조회 (기준: {by})")
        return customers
    
    # ========================================================================
    # 3. ML 전처리 및 분석
    # ========================================================================
    
    def preprocess(self) -> Dict[str, Any]:
        """데이터 전처리"""
        ic("🔧 전처리 시작")
        df = self.load_data()
        
        # 결측치 확인
        missing_values = df.isnull().sum()
        
        # 수치형 특성
        numeric_features = [
            'total_orders', 'total_revenue', 'avg_order_value',
            'last_order_days', 'contract_months', 'employee_count',
            'overdue_count', 'response_time_hours', 'meeting_count',
            'support_tickets', 'annual_growth_rate'
        ]
        
        # 범주형 특성
        categorical_features = ['company_type', 'industry', 'region', 'payment_terms']
        
        ic("✅ 전처리 완료")
        
        return {
            "total_rows": len(df),
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "missing_values": missing_values.to_dict(),
            "target": "churn_risk"
        }
    
    def split_data(self, test_size: float = 0.2) -> Dict[str, Any]:
        """학습/테스트 데이터 분할"""
        ic("✂️ 데이터 분할 시작")
        df = self.load_data()
        
        # 특성과 타겟 분리
        feature_columns = [
            'total_orders', 'total_revenue', 'avg_order_value',
            'last_order_days', 'contract_months', 'employee_count',
            'overdue_count', 'response_time_hours', 'meeting_count',
            'support_tickets', 'annual_growth_rate'
        ]
        
        X = df[feature_columns]
        y = df['churn_risk']
        
        # 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        ic(f"✅ 학습 데이터: {len(X_train)}개, 테스트 데이터: {len(X_test)}개")
        
        return {
            "train_size": len(X_train),
            "test_size": len(X_test),
            "train_churn_rate": float(y_train.mean()),
            "test_churn_rate": float(y_test.mean()),
            "features": feature_columns
        }
    
    # ========================================================================
    # 4. ML 모델링 및 예측
    # ========================================================================
    
    def train_model(self) -> Dict[str, Any]:
        """이탈 예측 모델 학습"""
        ic("🤖 모델 학습 시작")
        df = self.load_data()
        
        # 특성과 타겟 분리
        feature_columns = [
            'total_orders', 'total_revenue', 'avg_order_value',
            'last_order_days', 'contract_months', 'employee_count',
            'overdue_count', 'response_time_hours', 'meeting_count',
            'support_tickets', 'annual_growth_rate'
        ]
        
        X = df[feature_columns]
        y = df['churn_risk']
        
        # 학습/테스트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 모델 학습 (Random Forest)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # 예측 및 평가
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # 특성 중요도
        feature_importance = dict(zip(feature_columns, model.feature_importances_))
        sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        ic(f"✅ 모델 학습 완료 (정확도: {accuracy:.2%})")
        
        return {
            "model_type": "RandomForestClassifier",
            "accuracy": float(accuracy),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "feature_importance": sorted_importance
        }
    
    def predict_churn(self, customer_id: str) -> ChurnPrediction:
        """고객 이탈 확률 예측"""
        customer = self.get_customer_by_id(customer_id)
        
        if not customer:
            raise ValueError(f"고객 {customer_id}를 찾을 수 없습니다")
        
        # 고객 데이터를 딕셔너리로 변환
        customer_data = customer.model_dump()
        
        # 이탈 확률 예측
        churn_prob = self.model.predict_churn(customer_data)
        risk_level = self.model.get_risk_level(churn_prob)
        key_factors = self.model.get_key_factors(customer_data)
        recommendations = self.model.get_recommendations(risk_level, key_factors)
        
        prediction = ChurnPrediction(
            customer_id=customer_id,
            company_name=customer.company_name,
            churn_probability=churn_prob,
            risk_level=risk_level,
            key_factors=key_factors,
            recommendations=recommendations
        )
        
        ic(f"🎯 {customer_id} 이탈 확률: {churn_prob:.2%} ({risk_level})")
        return prediction
    
    # ========================================================================
    # 5. HuggingFace Datasets
    # ========================================================================
    
    def to_huggingface_dataset(self) -> Dataset:
        """HuggingFace Dataset으로 변환"""
        ic("🤗 HuggingFace Dataset 생성 중...")
        df = self.load_data()
        
        dataset = Dataset.from_pandas(df)
        ic(f"✅ Dataset 생성 완료: {len(dataset)}개 샘플")
        
        return dataset
    
    def to_huggingface_datasetdict(self, test_size: float = 0.2) -> DatasetDict:
        """HuggingFace DatasetDict으로 변환 (train/test 분할)"""
        ic("🤗 HuggingFace DatasetDict 생성 중...")
        df = self.load_data()
        
        # 학습/테스트 분할
        train_df, test_df = train_test_split(
            df, test_size=test_size, random_state=42, stratify=df['churn_risk']
        )
        
        dataset_dict = DatasetDict({
            'train': Dataset.from_pandas(train_df.reset_index(drop=True)),
            'test': Dataset.from_pandas(test_df.reset_index(drop=True))
        })
        
        ic(f"✅ DatasetDict 생성 완료: train={len(dataset_dict['train'])}, test={len(dataset_dict['test'])}")
        
        return dataset_dict

