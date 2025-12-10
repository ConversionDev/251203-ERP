"""
Seoul Service - 비즈니스 로직
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from app.seoul_crime.save.seoul_method import SeoulMethod
from app.seoul_crime.save.seoul_dataset import SeoulDataset
from app.seoul_crime.save.kakao_map_singleton import KakaoMapSingleton

logger = logging.getLogger(__name__)


class SeoulService:
    """서울 범죄 데이터 서비스"""
    
    def __init__(self):
        """초기화"""
        self.method = SeoulMethod()
        self.dataset = SeoulDataset()
        self.crime_rate_columns = ['살인검거율', '강도검거율', '강간검거율', '절도검거율', '폭력검거율']
        self.crime_columns = ['살인', '강도', '강간', '절도', '폭력']
        
    def get_cctv_top5(self) -> Dict[str, Any]:
        """CCTV 데이터 상위 5개 조회"""
        df = self.method.csv_to_df("cctv.csv")
        top5 = df.head(5)
        return {
            "status": "success",
            "data": top5.to_dict(orient="records"),
            "count": len(top5)
        }
    
    def get_crime_top5(self) -> Dict[str, Any]:
        """범죄 데이터 상위 5개 조회"""
        df = self.method.csv_to_df("crime.csv")
        data_df = df.iloc[4:].head(5)
        return {
            "status": "success",
            "data": data_df.to_dict(orient="records"),
            "count": len(data_df)
        }
    
    def get_pop_top5(self) -> Dict[str, Any]:
        """인구 데이터 상위 5개 조회"""
        df = self.method.xls_to_df("pop.xls")
        data_df = df.iloc[3:].head(5)
        return {
            "status": "success",
            "data": data_df.to_dict(orient="records"),
            "count": len(data_df)
        }
    
    def preprocess(self):
        """데이터 전처리 - CSV/XLS/XLSX 파일 로드 및 머지"""
        logger.info("🦝🦝전처리 시작")
        
        try:
            # 각 파일을 읽어서 데이터프레임으로 변환
            logger.info("CCTV 파일 읽기 시작...")
            cctv_df = self.method.csv_to_df("cctv.csv")
            cctv_df = cctv_df.drop(columns=['2013년도 이전', '2014년', '2015년', '2016년'])
            logger.info(f"CCTV 파일 읽기 완료: {cctv_df.shape}")
            
            logger.info("Crime 파일 읽기 시작...")
            crime_df = self.method.csv_to_df("crime.csv")
            
            # 관서명에 따른 경찰서 주소 찾기
            station_names = []  # 경찰서 관서명 리스트
            for name in crime_df['관서명']:
                station_names.append('서울' + str(name[:-1]) + '경찰서')
            
            logger.info(f"🔥💧경찰서 관서명 리스트: {station_names}")
            
            station_addrs = []
            station_lats = []
            station_lngs = []
            
            kmaps1 = KakaoMapSingleton()
            kmaps2 = KakaoMapSingleton()
            
            if kmaps1 is kmaps2:
                logger.info("동일한 객체 입니다.")
            else:
                logger.info("다른 객체 입니다.")
            
            kmaps = KakaoMapSingleton()  # 카카오맵 객체 생성
            
            for name in station_names:
                tmp = kmaps.geocode(name, language='ko')
                if tmp and len(tmp) > 0:
                    formatted_addr = tmp[0].get('formatted_address')
                    tmp_loc = tmp[0].get("geometry")
                    lat = tmp_loc['location']['lat']
                    lng = tmp_loc['location']['lng']
                    logger.info(f"{name}의 검색 결과: {formatted_addr} (위도: {lat}, 경도: {lng})")
                    station_addrs.append(formatted_addr)
                    station_lats.append(lat)
                    station_lngs.append(lng)
                else:
                    logger.warning(f"{name}의 검색 결과를 찾을 수 없습니다.")
                    station_addrs.append("")
                    station_lats.append(0.0)
                    station_lngs.append(0.0)
            
            logger.info(f"🔥💧자치구 리스트: {station_addrs}")
            
            gu_names = []
            for addr in station_addrs:
                if addr:  # 주소가 있는 경우만 처리
                    tmp = addr.split()
                    tmp_gu = [gu for gu in tmp if gu[-1] == '구']
                    if tmp_gu:
                        gu_names.append(tmp_gu[0])
                    else:
                        logger.warning(f"주소에서 '구'를 찾을 수 없습니다: {addr}")
                        gu_names.append("")
                else:
                    gu_names.append("")
            
            logger.info(f"🔥💧자치구 리스트 2: {gu_names}")
            
            # 자치구 컬럼을 제일 앞열에 추가
            crime_df.insert(0, '자치구', gu_names)
            
            # 관서명을 "중부서" → "중부경찰서" 형식으로 변경
            def convert_station_name(name):
                """관서명 변환: 중부서 → 중부경찰서"""
                name_str = str(name)
                if name_str.endswith('서'):
                    # 마지막 '서'를 제거하고 '경찰서' 추가
                    return name_str[:-1] + '경찰서'
                elif not name_str.endswith('경찰서'):
                    # '서'로 끝나지 않고 '경찰서'도 없으면 '경찰서' 추가
                    return name_str + '경찰서'
                return name_str
            
            crime_df['관서명'] = crime_df['관서명'].apply(convert_station_name)
            logger.info(f"관서명 변환 완료. 예시: {crime_df['관서명'].head().tolist()}")
            
            logger.info(f"Crime 파일 읽기 완료: {crime_df.shape}")
            
            # save 폴더에 저장 (현재 파일과 같은 디렉토리)
            from pathlib import Path
            # 현재 파일(seoul_service.py)이 있는 디렉토리를 save 경로로 사용
            current_file_dir = Path(__file__).parent.resolve()
            save_path = current_file_dir
            logger.info(f"저장 경로: {save_path}")
            logger.info(f"저장 경로 존재 여부: {save_path.exists()}")
            
            # 디렉토리 생성 (없으면 생성)
            save_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"저장 경로 생성 완료: {save_path}")
            
            crime_file_path = save_path / 'crime_with_gu.csv'
            logger.info(f"CSV 파일 저장 경로: {crime_file_path}")
            
            try:
                crime_df.to_csv(crime_file_path, index=False, encoding='utf-8-sig')
                logger.info(f"Crime 데이터 저장 완료: {crime_file_path}")
                logger.info(f"파일 존재 여부 확인: {crime_file_path.exists()}")
                if crime_file_path.exists():
                    file_size = crime_file_path.stat().st_size
                    logger.info(f"파일 크기: {file_size} bytes")
                    # 파일 내용 일부 확인
                    with open(crime_file_path, 'r', encoding='utf-8-sig') as f:
                        first_lines = [f.readline().strip() for _ in range(3)]
                    logger.info(f"파일 내용 확인 (첫 3줄): {first_lines}")
            except Exception as e:
                logger.error(f"CSV 저장 중 오류 발생: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            logger.info("Pop 파일 읽기 시작...")
            pop_df = self.method.xls_to_df("pop.xls")
            
            # POP 칼럼 편집
            # axis = 1방향으로 자치구 열과 4번째 컬럼만 남기고 모두 삭제
            # 자치구는 인덱스 1, 4번째 컬럼은 인덱스 3 ('인구')
            if '자치구' in pop_df.columns and len(pop_df.columns) > 3:
                columns_to_keep = ['자치구', pop_df.columns[3]]  # 자치구와 4번째 컬럼(인구)
                pop_df = pop_df[columns_to_keep]
            
            # axis = 0 방향으로 2,3,4 행 삭제 (인덱스 1,2,3)
            if len(pop_df) > 3:
                pop_df = pop_df.drop(index=[1, 2, 3]).reset_index(drop=True)
            
            logger.info(f"Pop 파일 읽기 완료: {pop_df.shape}")
            
        except FileNotFoundError as e:
            logger.error(f"파일을 찾을 수 없습니다: {e}")
            raise
        except Exception as e:
            logger.error(f"파일 읽기 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        # 데이터셋 객체에 저장
        self.method.dataset.cctv = cctv_df
        self.method.dataset.crime = crime_df
        self.method.dataset.pop = pop_df
        
        logger.info(f"CCTV 데이터: {cctv_df.shape}")
        logger.info(f"Crime 데이터: {crime_df.shape}")
        logger.info(f"Pop 데이터: {pop_df.shape}")
        logger.info("🦝🦝전처리 완료")
        
        # 각 데이터프레임의 상위 5개 행을 반환
        import math
        
        def safe_convert(value):
            """NaN, inf 값을 JSON 호환 값으로 변환"""
            if pd.isna(value):
                return None
            if isinstance(value, (np.integer, np.floating)):
                if math.isnan(value) or math.isinf(value):
                    return None
                return float(value) if isinstance(value, np.floating) else int(value)
            return value
        
        def clean_dict(d):
            """딕셔너리의 모든 값을 안전하게 변환"""
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            else:
                return safe_convert(d)
        
        def df_to_dict(df, head_rows=5, skip_rows=0):
            """
            데이터프레임을 딕셔너리로 변환
            
            Args:
                df: 데이터프레임
                head_rows: 표시할 행 수
                skip_rows: 건너뛸 행 수 (스키마 행 등)
            """
            # skip_rows 이후부터 head_rows만큼 가져오기
            if skip_rows > 0:
                head_data = df.iloc[skip_rows:skip_rows+head_rows].to_dict(orient='records')
            else:
                head_data = df.head(head_rows).to_dict(orient='records')
            return {
                "head": clean_dict(head_data),
                "columns": df.columns.tolist(),
                "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
                "null_counts": {col: int(count) for col, count in df.isnull().sum().items()}
            }
        
        # cctv와 pop 데이터 머지 전략
        # - cctv의 "기관명"과 pop의 "자치구"를 키로 사용
        # - 중복된 컬럼은 자동으로 제거됨
        # - 머지 후 "자치구" 컬럼만 유지하고 "기관명"은 제거
        logger.info("CCTV와 Pop 데이터 머지 시작...")
        cctv_pop_df = self.method.df_merge(
            right=cctv_df,  # 기준 데이터프레임
            left=pop_df,    # 병합할 데이터프레임
            left_on='자치구',  # pop의 키 컬럼
            right_on='기관명',  # cctv의 키 컬럼
            how='left',  # left join (cctv 기준)
            keep_key='left'  # "자치구" 컬럼만 유지
        )
        logger.info(f"CCTV-Pop 머지 완료: {cctv_pop_df.shape}")
        
        # 머지된 데이터를 데이터셋 객체에 저장
        self.method.dataset.cctv = cctv_df
        self.method.dataset.crime = crime_df
        self.method.dataset.pop = pop_df
        
        return {
            "message": "전처리 완료",
            "cctv": df_to_dict(cctv_df),
            "crime": df_to_dict(crime_df),
            "pop": df_to_dict(pop_df),
            "cctv_pop": df_to_dict(cctv_pop_df)
        }
    
    def get_cctv_pop_merged(self, limit: int = 5) -> Dict[str, Any]:
        """CCTV와 POP 머지된 데이터 조회"""
        # 데이터 로드
        cctv_df = self.method.csv_to_df("cctv.csv")
        pop_df = self.method.xls_to_df("pop.xls")
        
        # CCTV와 POP 머지
        cctv_pop_df = self.method.df_merge(
            right=cctv_df,  # 기준 데이터프레임
            left=pop_df,    # 병합할 데이터프레임
            left_on='자치구',  # pop의 키 컬럼
            right_on='기관명',  # cctv의 키 컬럼
            how='left',  # left join (cctv 기준)
            keep_key='left'  # "자치구" 컬럼만 유지
        )
        
        # 상위 N개 반환
        top_data = cctv_pop_df.head(limit)
        
        return {
            "status": "success",
            "data": top_data.to_dict(orient="records"),
            "count": len(top_data),
            "total_merged_rows": len(cctv_pop_df),
            "columns": list(cctv_pop_df.columns)
        }
    
    def add_district_to_crime(self) -> pd.DataFrame:
        """범죄 데이터에 자치구 컬럼 추가"""
        crime_df = self.method.csv_to_df("crime.csv")
        gu_names = []
        
        for name in crime_df['관서명']:
            gu = self.method.station_to_district(name)
            gu_names.append(gu)
        
        crime_df.insert(0, '자치구', gu_names)
        return crime_df
    
    def get_pop_edited(self, limit: int = 10) -> Dict[str, Any]:
        """POP 데이터 편집 결과 조회"""
        # POP 데이터 로드
        pop_df = self.method.xls_to_df("pop.xls")
        
        # POP 칼럼 편집
        # axis = 1방향으로 자치구 열과 4번째 컬럼만 남기고 모두 삭제
        # 자치구는 인덱스 1, 4번째 컬럼은 인덱스 3 ('인구')
        pop_columns = pop_df.columns.tolist()
        logger.info(f"[POP 데이터 편집 전] 컬럼: {pop_columns}, 행 수: {len(pop_df)}")
        
        if '자치구' in pop_df.columns and len(pop_df.columns) > 3:
            columns_to_keep = ['자치구', pop_df.columns[3]]  # 자치구와 4번째 컬럼(인구)
            pop_df = pop_df[columns_to_keep]
            logger.info(f"[POP 데이터 컬럼 편집] 자치구와 4번째 컬럼 유지: {columns_to_keep}")
        else:
            logger.warning(f"[POP 데이터 컬럼 편집] 컬럼 수가 4개 미만이거나 '자치구' 컬럼이 없습니다. 원본 컬럼 유지: {pop_columns}")
        
        # axis = 0 방향으로 2,3,4 행 삭제 (인덱스 1,2,3)
        if len(pop_df) > 3:
            pop_df = pop_df.drop(index=[1, 2, 3]).reset_index(drop=True)
            logger.info(f"[POP 데이터 행 삭제] 2,3,4행(인덱스 1,2,3) 삭제 완료")
        else:
            logger.warning(f"[POP 데이터 행 삭제] 행 수가 4개 미만입니다. 행 삭제 건너뜀")
        
        logger.info(f"[POP 데이터 행 편집 후] 컬럼: {list(pop_df.columns)}, 행 수: {len(pop_df)}")
        
        # 상위 N개 반환
        top_data = pop_df.head(limit)
        
        return {
            "status": "success",
            "data": top_data.to_dict(orient="records"),
            "count": len(top_data),
            "total_rows": len(pop_df),
            "columns": list(pop_df.columns),
            "original_columns_count": len(pop_columns),
            "edited_columns_count": len(pop_df.columns)
        }  
