from pathlib import Path
from app.titanic.titanic_dataset import TitanicDataset
import pandas as pd
import numpy as np
from icecream import ic
from pandas import DataFrame
from typing import Tuple


class TitanicMethod(object): 
    """타이타닉 데이터 전처리 메서드 클래스"""

    def __init__(self):
        """초기화 - train.csv 파일 경로 설정"""
        self.dataset = TitanicDataset()

    def read_csv(self, fname: str) -> pd.DataFrame:
        """CSV 파일을 읽어와서 DataFrame으로 반환"""
        base_path = Path(__file__).parent
        csv_path = base_path / fname
        return pd.read_csv(csv_path)

    def create_df(self, df: pd.DataFrame, label: str) -> pd.DataFrame:
        """Survived 값을 제거한 데이터프레임 반환"""
        return df.drop(columns=[label], errors='ignore')

    def create_label(self, df: pd.DataFrame, label: str) -> pd.DataFrame:
        """Survived 값만 가지는 답안지 데이터프레임 반환"""
        return df[[label]] if label in df.columns else pd.DataFrame()
       
    def drop_feature(self, this: TitanicDataset, *feature: str) -> TitanicDataset:
        """피처를 삭제하는 메서드 - train과 test를 함께 처리"""
        #이중 for문 axis(축, 열 삭제, 세로 방향 연산, aixs=0이면 가로방향 연산),
        # inplace = 내부에서 덮어쓰기
        [i.drop(j, axis=1, inplace=True) for j in feature for i in [this.train, this.test] if i is not None]
        return this

    def check_null(self, this: TitanicDataset) -> int:
        """전체 결측치(null값) 개수 반환"""
        total_null = sum([int(i.isnull().sum().sum()) for i in [this.train, this.test] if i is not None])
        return total_null

    # Feature 전처리 메서드 (척도: nominal, ordinal, interval, ratio)
    def pclass_ordinal(self, this: TitanicDataset) -> TitanicDataset:
        """
        Pclass: 객실 등급 (1, 2, 3) - 서열형 척도(ordinal)
        - 1등석 > 2등석 > 3등석 (생존률 관점에서 1이 가장 좋고 3이 가장 안 좋음)
        - int 타입으로 변환
        """
        [i.__setitem__("Pclass", i["Pclass"].astype(int)) for i in [this.train, this.test] if i is not None and "Pclass" in i.columns]
        return this

    def fare_ordinal(self, this: TitanicDataset) -> TitanicDataset:
        """
        Fare: 요금 - 구간화하여 서열형(ordinal)으로 변환
        - 결측치: 중앙값으로 채움
        - 사분위수로 4개 구간 binning (0, 1, 2, 3)
        """
        train_fare_median = this.train["Fare"].median() if this.train is not None and "Fare" in this.train.columns else None
        
        def process_fare(df):
            if df is not None and "Fare" in df.columns:
                fare_median = train_fare_median if train_fare_median is not None else df["Fare"].median()
                df["Fare"] = df["Fare"].fillna(fare_median)
                try:
                    df["Fare"] = pd.qcut(df["Fare"], q=4, labels=[0, 1, 2, 3], duplicates='drop')
                    df["Fare"] = df["Fare"].astype(int)
                except ValueError:
                    df["Fare"] = pd.cut(df["Fare"], bins=4, labels=[0, 1, 2, 3], duplicates='drop')
                    df["Fare"] = df["Fare"].astype(int)
        
        [process_fare(i) for i in [this.train, this.test]]
        return this

    def embarked_ordinal(self, this: TitanicDataset) -> TitanicDataset:
        """
        Embarked: 탑승 항구 (C, Q, S) - 명목형(nominal) 척도
        - 결측치: 최빈값(mode)으로 채움
        - label encoding으로 변환: C=1, Q=2, S=0
        """
        one_hot_cols = ["Embarked_C", "Embarked_Q", "Embarked_S"]
        [i.drop(columns=one_hot_cols, errors='ignore', inplace=True) for i in [this.train, this.test] if i is not None]
        
        train_embarked_mode = this.train["Embarked"].mode()[0] if this.train is not None and "Embarked" in this.train.columns and not this.train["Embarked"].mode().empty else "S"
        embarked_mapping = {"S": 0, "C": 1, "Q": 2}
        
        def process_embarked(df, mode_value):
            if df is not None and "Embarked" in df.columns:
                df["Embarked"] = df["Embarked"].fillna(mode_value)
                df["Embarked"] = df["Embarked"].map(embarked_mapping)
                df["Embarked"] = df["Embarked"].astype(int)
        
        [process_embarked(i, train_embarked_mode) for i in [this.train, this.test]]
        return this
    
    def gender_nominal(self, this: TitanicDataset) -> TitanicDataset:
        """
        Gender: 성별 (male, female) - 명목형(nominal) 척도
        - 이진 인코딩: male=1, female=0
        - Sex 컬럼을 Gender로 변환 (원본 컬럼 삭제)
        """
        def process_gender(df):
            if df is not None and "Sex" in df.columns:
                df["Gender"] = df["Sex"].map({"male": 1, "female": 0})
                df.drop(columns=["Sex"], inplace=True)
        
        [process_gender(i) for i in [this.train, this.test]]
        return this

    def age_ratio(self, this: TitanicDataset) -> TitanicDataset:
        """
        Age: 나이 - 구간화하여 서열형(ordinal)으로 변환
        - 결측치: 중앙값으로 채움
        - bins: [-1, 0, 5, 12, 18, 24, 35, 60, inf]
        - labels: 0=미상, 1=유아, 2=어린이, 3=청소년, 4=청년, 5=성인, 6=중년, 7=노년
        """
        bins = [-1, 0, 5, 12, 18, 24, 35, 60, np.inf]
        labels = [0, 1, 2, 3, 4, 5, 6, 7]
        train_age_median = this.train["Age"].median() if this.train is not None and "Age" in this.train.columns else None
        
        def process_age(df):
            if df is not None and "Age" in df.columns:
                age_median = train_age_median if train_age_median is not None else df["Age"].median()
                df["Age"] = df["Age"].fillna(age_median)
                df["Age"] = pd.cut(df["Age"], bins=bins, labels=labels, include_lowest=True)
                df["Age"] = df["Age"].astype(int)
        
        [process_age(i) for i in [this.train, this.test]]
        return this

    def title_nominal(self, this: TitanicDataset) -> TitanicDataset:
        """
        Title: 명칭 (Mr, Mrs, Miss, Master, Dr, etc.) - 명목형(nominal) 척도
        - Name 컬럼에서 정규표현식으로 Title 추출
        - 각 타이틀을 개별적으로 label encoding (0, 1, 2, ...)
        - 희소한 타이틀도 개별 처리하여 정보 보존
        - train과 test를 함께 처리하여 동일한 매핑 사용
        """
        # Name에서 Title 추출
        def extract_title(df):
            if df is not None and "Name" in df.columns:
                df["Title"] = df["Name"].str.extract(r',\s*([^\.]+)\.', expand=False)
                df["Title"] = df["Title"].fillna("Unknown")
        
        [extract_title(i) for i in [this.train, this.test]]
        
        # train과 test를 합쳐서 전체 타이틀 목록 생성 (일관성 유지)
        title_series = [i["Title"] for i in [this.train, this.test] if i is not None and "Title" in i.columns]
        all_titles = pd.concat(title_series, ignore_index=True) if title_series else pd.Series()
        unique_titles = all_titles.value_counts().index.tolist() if not all_titles.empty else []
        
        # Title을 숫자로 매핑 (0부터 시작)
        title_mapping = {title: idx for idx, title in enumerate(unique_titles)}
        
        def map_title(df):
            if df is not None and "Title" in df.columns:
                df["Title"] = df["Title"].map(title_mapping)
                df["Title"] = df["Title"].fillna(0)  # 매핑되지 않은 경우 0 (Unknown)
                df["Title"] = df["Title"].astype(int)
        
        [map_title(i) for i in [this.train, this.test]]
        return this
    