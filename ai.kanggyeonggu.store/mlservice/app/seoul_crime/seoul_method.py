import logging
import pandas as pd
import numpy as np
from pathlib import Path
from pandas import DataFrame
from app.seoul_crime.seoul_dataset import SeoulDataset
from app.seoul_crime.kakao_map_singleton import KakaoMapSingleton
import re

logger = logging.getLogger(__name__)

class SeoulMethod(object): 
    """서울 범죄 데이터 전처리 메서드 클래스"""

    def __init__(self):
        """초기화"""
        self.dataset = SeoulDataset()
        self.kakao_map = KakaoMapSingleton()

    # DS -> DF
    def csv_to_df(self, fname: str) -> pd.DataFrame:
        """CSV 파일을 읽어와서 DataFrame으로 반환"""
        # 경로 직접 지정: seoul_crime/data 디렉토리
        base_path = Path(__file__).parent / "data"
        csv_path = base_path / fname
        if not csv_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {csv_path}")
        return pd.read_csv(csv_path, encoding='utf-8-sig', quotechar='"')

    def xlsx_to_df(self, fname: str) -> pd.DataFrame:
        """XLSX 파일을 읽어와서 DataFrame으로 반환"""
        # 경로 직접 지정: seoul_crime/data 디렉토리
        base_path = Path(__file__).parent / "data"
        xlsx_path = base_path / fname
        if not xlsx_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {xlsx_path}")
        
        # 파일 확장자에 따라 엔진 선택
        file_ext = xlsx_path.suffix.lower()
        engine = 'xlrd' if file_ext == '.xls' else 'openpyxl'
        
        try:
            return pd.read_excel(xlsx_path, engine=engine)
        except ImportError:
            raise ImportError(f"{engine} 패키지가 필요합니다. 'pip install {engine}'을 실행해주세요.")
    
    def xls_to_df(self, fname: str) -> pd.DataFrame:
        """XLS 파일을 읽어와서 DataFrame으로 반환"""
        # 경로 직접 지정: seoul_crime/data 디렉토리
        base_path = Path(__file__).parent / "data"
        xls_path = base_path / fname
        if not xls_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {xls_path}")
        
        # 파일 확장자에 따라 엔진 선택
        file_ext = xls_path.suffix.lower()
        engine = 'xlrd' if file_ext == '.xls' else 'openpyxl'
        
        try:
            return pd.read_excel(xls_path, engine=engine)
        except ImportError:
            raise ImportError(f"{engine} 패키지가 필요합니다. 'pip install {engine}'을 실행해주세요.")
    
    def df_merge(self, right: pd.DataFrame, left: pd.DataFrame, left_on: str, right_on: str, how: str = 'left', keep_key: str = 'right') -> pd.DataFrame:
        """
        두 데이터프레임을 머지
        
        Args:
            right: 오른쪽 데이터프레임 (기준이 되는 데이터프레임)
            left: 왼쪽 데이터프레임 (병합할 데이터프레임)
            left_on: 왼쪽 데이터프레임의 키 컬럼명
            right_on: 오른쪽 데이터프레임의 키 컬럼명
            how: 머지 방식 ('left', 'right', 'inner', 'outer')
            keep_key: 머지 후 유지할 키 컬럼 ('right', 'left', 또는 둘 다 'both')
        
        Returns:
            머지된 데이터프레임
        """
        # 중복된 컬럼 확인 및 제거 (키 컬럼 제외)
        left_cols = set(left.columns) - {left_on}
        right_cols = set(right.columns) - {right_on}
        
        # 중복된 컬럼이 있으면 왼쪽 데이터프레임에서 제거
        overlap_cols = left_cols & right_cols
        if overlap_cols:
            logger.warning(f"중복된 컬럼이 발견되어 왼쪽 데이터프레임에서 제거합니다: {overlap_cols}")
            left = left.drop(columns=list(overlap_cols))
        
        # 머지 수행
        merged_df = pd.merge(
            right, 
            left, 
            left_on=right_on, 
            right_on=left_on, 
            how=how,
            suffixes=('', '_duplicate')  # 중복 방지용 접미사 (사실상 사용되지 않음)
        )
        
        # 접미사가 붙은 중복 컬럼 제거
        duplicate_cols = [col for col in merged_df.columns if col.endswith('_duplicate')]
        if duplicate_cols:
            merged_df = merged_df.drop(columns=duplicate_cols)
        
        # 키 컬럼 중복 제거 처리
        if keep_key == 'right':
            # 오른쪽 키 컬럼 유지, 왼쪽 키 컬럼 제거
            if left_on in merged_df.columns:
                merged_df = merged_df.drop(columns=[left_on])
        elif keep_key == 'left':
            # 왼쪽 키 컬럼 유지, 오른쪽 키 컬럼 제거
            if right_on in merged_df.columns:
                merged_df = merged_df.drop(columns=[right_on])
            # 왼쪽 키 컬럼명은 그대로 유지 (자치구)
        # keep_key == 'both'인 경우 둘 다 유지
        
        return merged_df
    
    def station_to_district(self, station_name: str) -> str:
        """
        관서명을 자치구로 변환 (기본 규칙 + 구글맵 API 예외 처리)
        
        Args:
            station_name: 경찰서 관서명 (예: "마포서", "방배서")
            
        Returns:
            자치구명 (예: "마포구", "강남구")
        """
        # 기본 규칙: "서" → "구" 변환
        if station_name.endswith("서"):
            district = station_name.replace("서", "구")
            
            # 유효한 자치구인지 확인 (CCTV 데이터의 자치구 목록과 비교)
            cctv_df = self.csv_to_df("cctv.csv")
            valid_districts = set(cctv_df['기관명'].tolist())
            
            # 유효한 자치구면 반환
            if district in valid_districts:
                return district
            
            # 유효하지 않으면 카카오맵 API로 확인 (예외 케이스)
            logger.info(f"예외 케이스 발견: {station_name}, 카카오맵 API 호출")
            return self._get_district_from_kakao_maps(station_name)
        
        # "서"로 끝나지 않으면 카카오맵 API로 확인
        return self._get_district_from_kakao_maps(station_name)
    
    def _get_district_from_kakao_maps(self, station_name: str) -> str:
        """
        카카오맵 API로 경찰서 위치 확인하여 자치구 추출
        
        Args:
            station_name: 경찰서명 (예: "방배서")
            
        Returns:
            자치구명 (예: "강남구")
        """
        try:
            # 검색어: "방배서 서울" 또는 "방배경찰서 서울"
            query = f"{station_name} 서울"
            
            # 카카오맵 API 호출
            geocode_result = self.kakao_map.geocode(query)
            
            if geocode_result and len(geocode_result) > 0:
                # 주소 컴포넌트에서 자치구 추출
                address_components = geocode_result[0].get('address_components', [])
                
                for component in address_components:
                    types = component.get('types', [])
                    # 'sublocality_level_1' 또는 'administrative_area_level_2'에서 구 추출
                    if 'sublocality_level_1' in types or 'administrative_area_level_2' in types:
                        long_name = component.get('long_name', '')
                        # "강남구" 형식에서 "구" 포함 여부 확인
                        if '구' in long_name:
                            return long_name
                        elif long_name.endswith('구'):
                            return long_name
                
                # formatted_address에서 추출 시도
                formatted_address = geocode_result[0].get('formatted_address', '')
                # "서울특별시 강남구 방배동" 형식에서 "강남구" 추출
                match = re.search(r'([가-힣]+구)', formatted_address)
                if match:
                    return match.group(1)
            
            logger.warning(f"카카오맵 API에서 자치구를 찾을 수 없음: {station_name}")
            # 실패 시 기본 규칙으로 시도
            if station_name.endswith("서"):
                return station_name.replace("서", "구")
            return station_name
            
        except Exception as e:
            logger.error(f"카카오맵 API 호출 실패: {station_name}, 오류: {e}")
            # 실패 시 기본 규칙으로 시도
            if station_name.endswith("서"):
                return station_name.replace("서", "구")
            return station_name
    