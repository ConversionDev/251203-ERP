import pandas as pd
from typing import Optional


class TitanicDataset:
    """타이타닉 데이터셋을 담는 클래스 - 여러 데이터셋을 처리할 수 있도록 확장 가능"""
    
    def __init__(self, train: Optional[pd.DataFrame] = None, test: Optional[pd.DataFrame] = None):
        """
        초기화
        Args:
            train: 학습용 데이터프레임
            test: 테스트용 데이터프레임
        """
        self.train = train
        self.test = test
