"""
Seoul Service - 비즈니스 로직
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import json
import folium
import os
from app.seoul_crime.seoul_method import SeoulMethod
from app.seoul_crime.seoul_dataset import SeoulDataset
from app.seoul_crime.kakao_map_singleton import KakaoMapSingleton
from app.seoul_crime.kakao_map_singleton import KakaoMapSingleton

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
            
            logger.info("🗺️ 카카오 맵 API를 사용하여 경찰서 주소 및 좌표 조회 시작...")
            kmaps1 = KakaoMapSingleton()
            kmaps2 = KakaoMapSingleton()
            
            if kmaps1 is kmaps2:
                logger.info("✅ KakaoMapSingleton: 동일한 객체입니다 (싱글톤 정상 작동)")
            else:
                logger.warning("⚠️ KakaoMapSingleton: 다른 객체입니다 (싱글톤 오류)")
            
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
            
            # 자치구 컬럼을 맨 뒤에 추가
            crime_df['자치구'] = gu_names
            
            # 관서명을 원래 형태로 유지 (변환하지 않음)
            logger.info(f"관서명 원본 유지. 예시: {crime_df['관서명'].head().tolist()}")
            
            # 중복 자치구 통합 (문자열 형식 유지)
            logger.info("🔄 중복 자치구 통합 시작...")
            crime_df = self._merge_duplicate_gu(crime_df)
            logger.info(f"중복 자치구 통합 완료: {crime_df.shape}")
            
            logger.info(f"Crime 파일 읽기 완료: {crime_df.shape}")
            
            # Pop 파일 읽기 (인구수 정보 추가를 위해)
            logger.info("Pop 파일 읽기 시작...")
            pop_df = self.method.xls_to_df("pop.xls")
            
            # POP 칼럼 편집
            if '자치구' in pop_df.columns and len(pop_df.columns) > 3:
                columns_to_keep = ['자치구', pop_df.columns[3]]  # 자치구와 4번째 컬럼(인구)
                pop_df = pop_df[columns_to_keep]
            
            # axis = 0 방향으로 2,3,4 행 삭제 (인덱스 1,2,3)
            if len(pop_df) > 3:
                pop_df = pop_df.drop(index=[1, 2, 3]).reset_index(drop=True)
            
            logger.info(f"Pop 파일 읽기 완료: {pop_df.shape}")
            
            # 1. 범죄 데이터와 인구 데이터 merge (인구수 컬럼 추가)
            logger.info("범죄 데이터와 인구 데이터 merge 시작...")
            # 인구 컬럼명 정리
            pop_columns = pop_df.columns.tolist()
            if len(pop_columns) > 1:
                pop_col = pop_columns[1]
            else:
                pop_col = pop_columns[0]
            
            # 인구 데이터 정리
            pop_clean = pop_df[['자치구', pop_col]].copy()
            pop_clean.columns = ['자치구', '인구']
            
            # 자치구명 정규화 함수 (공백 제거, 따옴표 제거)
            def normalize_gu_name(name):
                if pd.isna(name):
                    return ""
                name_str = str(name).strip()
                # 따옴표 제거
                name_str = name_str.strip('"').strip("'")
                # 앞뒤 공백 제거
                name_str = name_str.strip()
                return name_str
            
            # 자치구명 정규화 적용
            pop_clean['자치구'] = pop_clean['자치구'].apply(normalize_gu_name)
            crime_df['자치구'] = crime_df['자치구'].apply(normalize_gu_name)
            
            # 인구 데이터를 숫자로 변환 (쉼표 제거)
            def str_to_float(val):
                if pd.isna(val):
                    return 0.0
                str_val = str(val).replace(',', '').strip()
                try:
                    return float(str_val)
                except (ValueError, TypeError):
                    return 0.0
            
            pop_clean['인구'] = pop_clean['인구'].apply(str_to_float)
            
            # pop_clean과 crime_df의 자치구 목록 확인
            pop_gu_list = pop_clean['자치구'].tolist()
            crime_gu_list = crime_df['자치구'].unique().tolist()
            
            logger.info(f"📊 인구 데이터 자치구 목록: {pop_gu_list}")
            logger.info(f"📊 범죄 데이터 자치구 목록: {crime_gu_list}")
            
            # 종로구 특별 처리: pop.xls에서 종로구를 찾기 (다양한 표기 고려)
            jongno_found = False
            jongno_pop_value = None
            
            # 1. 정확히 "종로구"로 매칭되는지 확인
            if '종로구' in pop_gu_list:
                jongno_found = True
                jongno_pop_value = pop_clean[pop_clean['자치구'] == '종로구']['인구'].iloc[0]
                logger.info(f"✅ 종로구 인구 데이터 발견: {jongno_pop_value:,.0f}명")
            else:
                # 2. "종로"로 시작하는 자치구 찾기
                jongno_variants = [gu for gu in pop_gu_list if '종로' in gu]
                if jongno_variants:
                    jongno_found = True
                    jongno_pop_value = pop_clean[pop_clean['자치구'] == jongno_variants[0]]['인구'].iloc[0]
                    logger.info(f"✅ 종로구 변형 발견 ('{jongno_variants[0]}'): {jongno_pop_value:,.0f}명")
                    # pop_clean의 해당 자치구명을 "종로구"로 변경
                    pop_clean.loc[pop_clean['자치구'] == jongno_variants[0], '자치구'] = '종로구'
            
            # 3. 종로구가 범죄 데이터에 있고, pop_clean에 없거나 값이 다르면 보정
            if '종로구' in crime_gu_list:
                if '종로구' not in pop_clean['자치구'].tolist():
                    # 종로구가 없으면 추가 (162,820)
                    jongno_pop_value = 162820.0
                    new_row = pd.DataFrame({'자치구': ['종로구'], '인구': [jongno_pop_value]})
                    pop_clean = pd.concat([pop_clean, new_row], ignore_index=True)
                    logger.info(f"✅ 종로구 인구 데이터 추가: {jongno_pop_value:,.0f}명")
                else:
                    # 종로구가 있으면 값 확인 및 보정
                    current_pop = pop_clean[pop_clean['자치구'] == '종로구']['인구'].iloc[0]
                    if current_pop != 162820.0:
                        pop_clean.loc[pop_clean['자치구'] == '종로구', '인구'] = 162820.0
                        logger.info(f"✅ 종로구 인구 데이터 보정: {current_pop:,.0f} → 162,820명")
                    else:
                        logger.info(f"✅ 종로구 인구 데이터 확인: {current_pop:,.0f}명 (정상)")
            
            # 자치구명 매핑 테이블 생성 (유사한 이름 매칭) - 종로구 제외
            gu_mapping = {}
            for crime_gu in crime_gu_list:
                if crime_gu and crime_gu != '종로구' and crime_gu not in pop_clean['자치구'].tolist():
                    # 유사한 자치구명 찾기
                    similar_gu = [gu for gu in pop_clean['자치구'].tolist() 
                                 if crime_gu in gu or gu in crime_gu or 
                                 crime_gu.replace('구', '') == gu.replace('구', '')]
                    if similar_gu:
                        gu_mapping[crime_gu] = similar_gu[0]
                        logger.info(f"✅ 자치구명 매핑: '{crime_gu}' → '{similar_gu[0]}'")
            
            # pop_clean의 자치구명을 매핑 테이블로 변환
            if gu_mapping:
                reverse_mapping = {v: k for k, v in gu_mapping.items()}
                pop_clean['자치구'] = pop_clean['자치구'].apply(
                    lambda x: reverse_mapping.get(x, x)
                )
            
            # 최종 확인: 종로구가 pop_clean에 있는지 확인
            final_pop_gu_list = pop_clean['자치구'].tolist()
            if '종로구' in crime_gu_list:
                if '종로구' in final_pop_gu_list:
                    jongno_final_pop = pop_clean[pop_clean['자치구'] == '종로구']['인구'].iloc[0]
                    logger.info(f"✅ 최종 확인: 종로구 인구 데이터 = {jongno_final_pop:,.0f}명")
                else:
                    logger.error(f"❌ 최종 확인 실패: 종로구가 pop_clean에 없습니다!")
            
            # 범죄 데이터와 인구 데이터 merge
            crime_df_with_pop = pd.merge(
                crime_df,
                pop_clean,
                on='자치구',
                how='left'  # 범죄 데이터 기준 (인구 데이터가 없어도 유지)
            )
            logger.info(f"범죄-인구 데이터 merge 완료: {crime_df_with_pop.shape}")
            logger.info(f"인구수 컬럼 추가 확인: {'인구' in crime_df_with_pop.columns}")
            
            # merge 결과 검증
            missing_pop = crime_df_with_pop[crime_df_with_pop['인구'].isna() | (crime_df_with_pop['인구'] == 0)]
            if len(missing_pop) > 0:
                missing_gu_list = missing_pop['자치구'].unique().tolist()
                logger.warning(f"⚠️ 인구 데이터가 없는 자치구: {missing_gu_list}")
            else:
                logger.info(f"✅ 모든 자치구의 인구 데이터가 정상적으로 매칭되었습니다.")
            
            # 종로구 인구 데이터 최종 확인
            if '종로구' in crime_df_with_pop['자치구'].tolist():
                jongno_row = crime_df_with_pop[crime_df_with_pop['자치구'] == '종로구']
                if len(jongno_row) > 0:
                    jongno_pop_final = jongno_row['인구'].iloc[0]
                    logger.info(f"✅ CSV 저장 전 종로구 인구 데이터 확인: {jongno_pop_final:,.0f}명")
            
            # save 폴더에 파일 저장 (덮어쓰기)
            save_path = Path(__file__).parent / "save"
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 1. CSV 파일 저장 (덮어쓰기)
            try:
                crime_file_path = save_path / 'crime_with_gu.csv'
                crime_df_with_pop.to_csv(crime_file_path, index=False, encoding='utf-8-sig')
                logger.info(f"Crime 데이터 저장 완료 (인구수 포함): {crime_file_path}")
            except Exception as e:
                logger.error(f"CSV 저장 중 오류 발생: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # 2. 히트맵 생성 및 저장 (덮어쓰기)
            try:
                self.generate_heatmap(crime_df_with_pop, save_path)
                logger.info(f"히트맵 저장 완료: {save_path / 'crime_heatmap.png'}")
            except Exception as e:
                logger.warning(f"히트맵 생성 중 오류 발생 (계속 진행): {e}")
                import traceback
                logger.warning(traceback.format_exc())
            
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
        self.method.dataset.crime = crime_df_with_pop  # 인구수 포함된 데이터프레임 저장
        self.method.dataset.pop = pop_clean  # 정리된 인구 데이터 저장
        
        # 히트맵과 동일한 데이터를 사용하기 위해 인스턴스 변수로 저장
        self.crime_df_with_pop = crime_df_with_pop
        
        logger.info(f"CCTV 데이터: {cctv_df.shape}")
        logger.info(f"Crime 데이터: {crime_df_with_pop.shape} (인구수 포함)")
        logger.info(f"Pop 데이터: {pop_clean.shape}")
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
            left=pop_clean,    # 병합할 데이터프레임 (정리된 인구 데이터)
            left_on='자치구',  # pop의 키 컬럼
            right_on='기관명',  # cctv의 키 컬럼
            how='left',  # left join (cctv 기준)
            keep_key='left'  # "자치구" 컬럼만 유지
        )
        logger.info(f"CCTV-Pop 머지 완료: {cctv_pop_df.shape}")
        
        # 머지된 데이터를 데이터셋 객체에 저장 (이미 위에서 저장됨)
        # self.method.dataset.cctv = cctv_df
        # self.method.dataset.crime = crime_df_with_pop
        # self.method.dataset.pop = pop_clean
        
        return {
            "message": "전처리 완료",
            "cctv": df_to_dict(cctv_df),
            "crime": df_to_dict(crime_df_with_pop),  # 인구수 포함된 데이터
            "pop": df_to_dict(pop_clean),  # 정리된 인구 데이터
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
    
    def _merge_duplicate_gu(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        중복된 자치구를 하나로 통합 (문자열 형식 유지)
        
        Args:
            df: 자치구 컬럼이 포함된 범죄 데이터프레임
            
        Returns:
            중복 자치구가 통합된 데이터프레임
        """
        # 숫자 컬럼 목록 (쉼표 포함 문자열)
        numeric_columns = [
            '살인 발생', '살인 검거', '강도 발생', '강도 검거', 
            '강간 발생', '강간 검거', '절도 발생', '절도 검거',
            '폭력 발생', '폭력 검거'
        ]
        
        # 숫자 컬럼만 존재하는 것만 필터링
        numeric_cols = [col for col in numeric_columns if col in df.columns]
        
        def sum_string_numbers(series):
            """문자열 숫자들을 합산하고 다시 문자열로 반환"""
            total = 0
            for val in series:
                if pd.notna(val):
                    # 쉼표 제거 후 정수 변환 (내부 계산용)
                    str_val = str(val).replace(',', '').strip()
                    try:
                        total += int(str_val)
                    except (ValueError, TypeError):
                        pass
            # 결과를 쉼표 포함 문자열로 포맷팅
            return f"{total:,}"
        
        def first_value(series):
            """첫 번째 값 반환"""
            return series.iloc[0] if len(series) > 0 else ''
        
        # 집계 함수 정의
        agg_dict = {}
        for col in numeric_cols:
            agg_dict[col] = sum_string_numbers
        agg_dict['관서명'] = first_value
        
        # 자치구별로 그룹화하여 집계
        grouped = df.groupby('자치구', as_index=False).agg(agg_dict)
        
        # 컬럼 순서 유지 (원본 순서대로)
        original_cols = df.columns.tolist()
        # 자치구를 제외한 컬럼 순서
        other_cols = [col for col in original_cols if col != '자치구']
        # 자치구를 맨 뒤로
        final_cols = [col for col in other_cols if col in grouped.columns] + ['자치구']
        grouped = grouped[final_cols]
        
        logger.info(f"중복 자치구 통합: {len(df)}개 행 → {len(grouped)}개 행")
        
        return grouped
    
    def generate_heatmap(self, df: pd.DataFrame, save_path: Path) -> str:
        """
        범죄 발생율 및 검거율 히트맵 생성 및 PNG 저장 (서브플롯 방식)
        
        Args:
            df: 범죄 데이터프레임 (crime_with_gu.csv 형식, 인구 포함)
            save_path: 저장 경로 (Path 객체)
            
        Returns:
            저장된 히트맵 파일 경로
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            from matplotlib import font_manager
        except ImportError as e:
            logger.error(f"시각화 라이브러리 import 실패: {e}")
            raise
        
        logger.info("📊 히트맵 생성 시작 (범죄 발생율 + 검거율)...")
        
        # 1. 데이터 전처리
        crime_types = ['살인', '강도', '강간', '절도', '폭력']
        crime_occur_cols = [f'{ct} 발생' for ct in crime_types]
        crime_arrest_cols = [f'{ct} 검거' for ct in crime_types]
        
        # 필요한 컬럼 확인
        required_cols = ['자치구', '인구'] + crime_occur_cols + crime_arrest_cols
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"필수 컬럼이 없습니다: {missing_cols}")
        
        # 데이터프레임 복사
        work_df = df[required_cols].copy()
        
        # 쉼표 포함 문자열을 숫자로 변환
        def str_to_float(val):
            if pd.isna(val):
                return 0.0
            str_val = str(val).replace(',', '').strip()
            try:
                return float(str_val)
            except (ValueError, TypeError):
                return 0.0
        
        # 모든 숫자 컬럼 변환
        for col in crime_occur_cols + crime_arrest_cols + ['인구']:
            work_df[col] = work_df[col].apply(str_to_float)
        
        # 2. 범죄 발생율 계산 (10만명당)
        rate_df = work_df[['자치구']].copy()
        for i, crime_type in enumerate(crime_types):
            occur_col = crime_occur_cols[i]
            rate_col = f'{crime_type} 발생율'
            # 범죄율 = (범죄 발생 건수 ÷ 인구) × 100,000
            # 인구가 0이거나 NaN인 경우 처리
            mask = (work_df['인구'] > 0) & (work_df['인구'].notna())
            rate_df[rate_col] = 0.0  # 기본값 0
            rate_df.loc[mask, rate_col] = (
                work_df.loc[mask, occur_col] / work_df.loc[mask, '인구'] * 100000
            ).round(1)
            
            # 인구가 없거나 0인 자치구 로깅
            missing_mask = ~mask
            if missing_mask.any():
                missing_gu = work_df.loc[missing_mask, '자치구'].tolist()
                logger.warning(f"⚠️ {crime_type} 발생율 계산: 인구 데이터가 없는 자치구 → 0으로 설정: {missing_gu}")
        
        rate_df = rate_df.set_index('자치구')
        rate_df = rate_df.rename(columns={f'{ct} 발생율': ct for ct in crime_types})
        
        # 2-1. 범죄 발생율 정규화 (최댓값을 1로 설정, 나머지는 비율로 변환)
        # 각 범죄 유형별로 최댓값을 찾아서 정규화
        rate_df_normalized = rate_df.copy()
        for crime_type in crime_types:
            if crime_type in rate_df_normalized.columns:
                # 음수 값 제거 (0으로 설정)
                rate_df_normalized.loc[rate_df_normalized[crime_type] < 0, crime_type] = 0.0
                
                max_value = rate_df_normalized[crime_type].max()
                if max_value > 0:
                    # 정규화: value / max_value (0~1 사이 값)
                    rate_df_normalized[crime_type] = (rate_df_normalized[crime_type] / max_value).round(4)
                    # 정규화 후에도 0~1 범위를 벗어나는 값 보정
                    rate_df_normalized.loc[rate_df_normalized[crime_type] < 0, crime_type] = 0.0
                    rate_df_normalized.loc[rate_df_normalized[crime_type] > 1, crime_type] = 1.0
                else:
                    # 최댓값이 0이면 모두 0으로 설정
                    rate_df_normalized[crime_type] = 0.0
        
        # 3. 검거율 계산 (%)
        arrest_df = work_df[['자치구']].copy()
        for i, crime_type in enumerate(crime_types):
            occur_col = crime_occur_cols[i]
            arrest_col = crime_arrest_cols[i]
            arrest_rate_col = f'{crime_type} 검거율'
            # 검거율 = (검거 건수 ÷ 발생 건수) × 100
            mask = work_df[occur_col] > 0
            arrest_df[arrest_rate_col] = 0.0
            arrest_df.loc[mask, arrest_rate_col] = (
                work_df.loc[mask, arrest_col] / work_df.loc[mask, occur_col] * 100
            ).round(1)
        
        arrest_df = arrest_df.set_index('자치구')
        arrest_df = arrest_df.rename(columns={f'{ct} 검거율': ct for ct in crime_types})
        
        # 4. 한글 폰트 설정
        plt.rcParams['axes.unicode_minus'] = False
        font_path = None
        font_name = None
        
        data_path = Path(__file__).parent / 'data'
        possible_font_paths = [
            data_path / 'NanumGothic.ttf',
            data_path / 'NanumGothic-Regular.ttf',
            data_path / 'malgun.ttf',
            Path(__file__).parent.parent.parent / 'fonts' / 'NanumGothic.ttf',
        ]
        
        for font_file in possible_font_paths:
            if font_file.exists():
                font_path = str(font_file)
                font_prop = font_manager.FontProperties(fname=font_path)
                font_name = font_prop.get_name()
                plt.rcParams['font.family'] = font_name
                break
        
        if font_path is None:
            try:
                malgun_fonts = [f for f in font_manager.fontManager.ttflist 
                              if 'malgun' in f.name.lower() or 'gulim' in f.name.lower()]
                if malgun_fonts:
                    font_name = malgun_fonts[0].name
                    plt.rcParams['font.family'] = font_name
                else:
                    nanum_fonts = [f for f in font_manager.fontManager.ttflist 
                                 if 'nanum' in f.name.lower()]
                    if nanum_fonts:
                        font_name = nanum_fonts[0].name
                        plt.rcParams['font.family'] = font_name
            except Exception:
                pass
        
        if font_path is None and font_name is None:
            plt.rcParams['font.family'] = 'DejaVu Sans'
        
        if font_path:
            font_prop = font_manager.FontProperties(fname=font_path)
        else:
            font_prop = None
        
        # 5. 서브플롯으로 히트맵 생성
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
        
        # 상단: 범죄 발생율 히트맵 (정규화 분포)
        sns.heatmap(
            rate_df_normalized.T,
            annot=True,
            fmt='.4f',
            cmap='YlOrRd',
            cbar_kws={'label': '범죄 발생율 (정규화: 최댓값=1)'},
            linewidths=0.5,
            linecolor='gray',
            square=False,
            ax=ax1,
            vmin=0,
            vmax=1
        )
        
        if font_prop:
            ax1.set_title('서울시 자치구별 범죄 발생율 (정규화 분포, 최댓값=1)', 
                         fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
            ax1.set_xlabel('자치구', fontsize=12, fontweight='bold', fontproperties=font_prop)
            ax1.set_ylabel('범죄 유형', fontsize=12, fontweight='bold', fontproperties=font_prop)
        else:
            ax1.set_title('서울시 자치구별 범죄 발생율 (정규화 분포, 최댓값=1)', 
                         fontsize=16, fontweight='bold', pad=20)
            ax1.set_xlabel('자치구', fontsize=12, fontweight='bold')
            ax1.set_ylabel('범죄 유형', fontsize=12, fontweight='bold')
        
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
        
        # 하단: 검거율 히트맵
        sns.heatmap(
            arrest_df.T,
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            cbar_kws={'label': '검거율 (%)'},
            linewidths=0.5,
            linecolor='gray',
            square=False,
            ax=ax2
        )
        
        if font_prop:
            ax2.set_title('서울시 자치구별 범죄 검거율 (%)', 
                         fontsize=16, fontweight='bold', pad=20, fontproperties=font_prop)
            ax2.set_xlabel('자치구', fontsize=12, fontweight='bold', fontproperties=font_prop)
            ax2.set_ylabel('범죄 유형', fontsize=12, fontweight='bold', fontproperties=font_prop)
        else:
            ax2.set_title('서울시 자치구별 범죄 검거율 (%)', 
                         fontsize=16, fontweight='bold', pad=20)
            ax2.set_xlabel('자치구', fontsize=12, fontweight='bold')
            ax2.set_ylabel('범죄 유형', fontsize=12, fontweight='bold')
        
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # 6. PNG 저장 (덮어쓰기)
        heatmap_file_path = save_path / 'crime_heatmap.png'
        plt.savefig(heatmap_file_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"히트맵 저장 완료: {heatmap_file_path}")
        logger.info(f"히트맵 크기: {heatmap_file_path.stat().st_size} bytes")
        
        return str(heatmap_file_path)
    
    def generate_crime_rate_map(self, crime_df: pd.DataFrame, pop_df: pd.DataFrame = None, save_path: Path = None) -> str:
        """
        자치구별 인구 대비 범죄율 지도 생성 (방법 B: 범죄 유형별 다중 레이어)
        
        Args:
            crime_df: 범죄 데이터프레임 (crime_with_gu.csv 형식, 인구수 포함 가능)
            pop_df: 인구 데이터프레임 (자치구, 인구 컬럼 포함, crime_df에 인구수가 없을 때 사용)
            save_path: HTML 파일 저장 경로 (Path 객체, None이면 자동으로 save 폴더 사용)
            
        Returns:
            지도 HTML 문자열
        """
        try:
            logger.info("🗺️ 범죄율 지도 생성 시작...")
            
            # save_path가 없으면 자동으로 설정
            if save_path is None:
                save_path = Path(__file__).parent / "save"
                save_path.mkdir(parents=True, exist_ok=True)
            
            # 1. 데이터 통합
            logger.info("데이터 통합 시작...")
            
            # 2. CSV에 인구수가 있는지 확인
            if '인구' in crime_df.columns:
                logger.info("✅ CSV에 인구수 컬럼이 있습니다. CSV의 인구수 사용")
                # CSV의 인구수 사용 (검거 데이터도 포함)
                crime_cols = ['자치구'] + [col for col in crime_df.columns if '발생' in col or '검거' in col] + ['인구']
                merged_df = crime_df[crime_cols].copy()
                
                # 인구 데이터를 숫자로 변환 (쉼표 제거)
                def str_to_float(val):
                    if pd.isna(val):
                        return 0.0
                    str_val = str(val).replace(',', '').strip()
                    try:
                        return float(str_val)
                    except (ValueError, TypeError):
                        return 0.0
                
                merged_df['인구'] = merged_df['인구'].apply(str_to_float)
                logger.info(f"CSV 인구수 사용. 데이터 shape: {merged_df.shape}")
                logger.info(f"포함된 컬럼: {merged_df.columns.tolist()}")
            else:
                logger.info("⚠️ CSV에 인구수 컬럼이 없습니다. pop_df에서 인구수 로드")
                # pop_df에서 인구수 로드
                pop_columns = pop_df.columns.tolist()
                logger.info(f"인구 데이터 컬럼: {pop_columns}")
                
                # 인구 컬럼 찾기
                if len(pop_columns) > 1:
                    pop_col = pop_columns[1] if len(pop_columns) > 1 else pop_columns[0]
                else:
                    pop_col = pop_columns[0]
                
                # 인구 데이터 정리
                pop_clean = pop_df[['자치구', pop_col]].copy()
                pop_clean.columns = ['자치구', '인구']
                
                # 인구 데이터를 숫자로 변환
                def str_to_float(val):
                    if pd.isna(val):
                        return 0.0
                    str_val = str(val).replace(',', '').strip()
                    try:
                        return float(str_val)
                    except (ValueError, TypeError):
                        return 0.0
                
                pop_clean['인구'] = pop_clean['인구'].apply(str_to_float)
                logger.info(f"인구 데이터 정리 완료: {pop_clean.shape}")
                
                # 범죄 데이터와 인구 데이터 병합
                # 범죄 발생 및 검거 데이터 모두 포함
                crime_cols = ['자치구'] + [col for col in crime_df.columns if '발생' in col or '검거' in col]
                merged_df = pd.merge(
                    crime_df[crime_cols],
                    pop_clean,
                    on='자치구',
                    how='inner'
                )
                logger.info(f"데이터 통합 완료: {merged_df.shape}")
                logger.info(f"통합된 컬럼: {merged_df.columns.tolist()}")
            
            logger.info(f"통합된 자치구: {merged_df['자치구'].tolist()}")
            logger.info(f"인구수 샘플: {merged_df[['자치구', '인구']].head(5).to_dict('records')}")
            
            # 2. 범죄율 계산
            logger.info("범죄율 계산 시작...")
            crime_types = ['살인 발생', '강도 발생', '강간 발생', '절도 발생', '폭력 발생']
            
            # 히트맵과 동일하게 모든 숫자 컬럼을 float로 변환
            def str_to_float(val):
                if pd.isna(val):
                    return 0.0
                str_val = str(val).replace(',', '').strip()
                try:
                    return float(str_val)
                except (ValueError, TypeError):
                    return 0.0
            
            # 범죄 발생 및 검거 건수를 숫자로 변환 (히트맵과 동일하게 float 사용)
            for crime_type in crime_types:
                if crime_type in merged_df.columns:
                    merged_df[crime_type] = merged_df[crime_type].apply(str_to_float)
            
            # 검거 데이터도 숫자로 변환 (히트맵과 동일하게 float 사용)
            crime_arrest_types = ['살인 검거', '강도 검거', '강간 검거', '절도 검거', '폭력 검거']
            for arrest_col in crime_arrest_types:
                if arrest_col in merged_df.columns:
                    merged_df[arrest_col] = merged_df[arrest_col].apply(str_to_float)
            
            # 범죄율 계산 (10만명당)
            rate_df = merged_df[['자치구', '인구']].copy()
            
            for crime_type in crime_types:
                if crime_type in merged_df.columns:
                    rate_col = crime_type.replace(' 발생', ' 발생율')
                    # 범죄율 = (범죄 발생 건수 ÷ 인구) × 100,000
                    # 히트맵과 동일하게 인구가 0이거나 NaN인 경우 처리
                    mask = (merged_df['인구'] > 0) & (merged_df['인구'].notna())
                    rate_df[rate_col] = 0.0  # 기본값 0
                    rate_df.loc[mask, rate_col] = (
                        merged_df.loc[mask, crime_type] / merged_df.loc[mask, '인구'] * 100000
                    ).round(1)
                    logger.info(f"{rate_col} 계산 완료")
            
            # 범죄 발생율 정규화 (히트맵과 동일하게)
            # 히트맵과 동일한 방식으로 정규화: 각 범죄 유형별로 최댓값을 1로 설정
            crime_type_names = ['살인', '강도', '강간', '절도', '폭력']
            rate_cols = [f'{ct} 발생율' for ct in crime_type_names]
            
            # 각 범죄 유형별로 정규화 (히트맵과 동일한 로직)
            for i, crime_type_name in enumerate(crime_type_names):
                rate_col = rate_cols[i]
                if rate_col in rate_df.columns:
                    # 음수 값 제거 (0으로 설정)
                    rate_df.loc[rate_df[rate_col] < 0, rate_col] = 0.0
                    
                    max_value = rate_df[rate_col].max()
                    if max_value > 0:
                        # 정규화: value / max_value (0~1 사이 값)
                        rate_df[rate_col] = (rate_df[rate_col] / max_value).round(4)
                        # 정규화 후에도 0~1 범위를 벗어나는 값 보정
                        rate_df.loc[rate_df[rate_col] < 0, rate_col] = 0.0
                        rate_df.loc[rate_df[rate_col] > 1, rate_col] = 1.0
                    else:
                        # 최댓값이 0이면 모두 0으로 설정
                        rate_df[rate_col] = 0.0
            
            # 총 범죄 발생율 계산 (정규화된 값들의 평균 - 히트맵과 일치시키기 위해)
            # 히트맵은 각 범죄 유형별 정규화된 값을 보여주므로, 지도에서도 평균값 사용
            total_crime_cols = [col for col in rate_df.columns if '발생율' in col and col != '총 범죄 발생율']
            rate_df['총 범죄 발생율'] = rate_df[total_crime_cols].mean(axis=1).round(4)
            logger.info("총 범죄 발생율 계산 완료 (정규화된 값들의 평균)")
            
            logger.info(f"범죄율 계산 완료 (정규화 적용): {rate_df.shape}")
            
            # 검거율 계산 추가 (히트맵과 동일한 방식)
            logger.info("검거율 계산 시작...")
            # merged_df와 동일한 인덱스를 유지하면서 자치구만 복사
            arrest_rate_df = pd.DataFrame({'자치구': merged_df['자치구'].values}, index=merged_df.index)
            
            for i, crime_type in enumerate(crime_types):
                occur_col = crime_type  # '살인 발생', '강도 발생', ...
                arrest_col = crime_arrest_types[i]  # '살인 검거', '강도 검거', ...
                arrest_rate_col = crime_type.replace(' 발생', ' 검거율')  # '살인 검거율', '강도 검거율', ...
                
                if occur_col in merged_df.columns and arrest_col in merged_df.columns:
                    # 검거율 = (검거 건수 ÷ 발생 건수) × 100
                    # 인덱스가 동일하므로 직접 할당 가능
                    mask = merged_df[occur_col] > 0
                    arrest_rate_df[arrest_rate_col] = 0.0
                    arrest_rate_df.loc[mask, arrest_rate_col] = (
                        merged_df.loc[mask, arrest_col] / merged_df.loc[mask, occur_col] * 100
                    ).round(1)
                    logger.info(f"{arrest_rate_col} 계산 완료: 합계={arrest_rate_df[arrest_rate_col].sum():.1f}%, 평균={arrest_rate_df[arrest_rate_col].mean():.1f}%")
                    logger.info(f"   샘플 값 (상위 3개): {arrest_rate_df.loc[mask, ['자치구', arrest_rate_col]].head(3).to_dict('records')}")
                else:
                    logger.warning(f"⚠️ {arrest_rate_col} 계산 실패: {occur_col} 또는 {arrest_col} 컬럼이 없습니다.")
                    logger.warning(f"   merged_df 컬럼: {merged_df.columns.tolist()}")
            
            # rate_df에 검거율 추가 (자치구 기준으로 merge)
            rate_df = pd.merge(
                rate_df,
                arrest_rate_df,
                on='자치구',
                how='left'
            )
            
            # 검거율이 없는 경우 0으로 설정
            arrest_cols = [col for col in arrest_rate_df.columns if col != '자치구']
            for col in arrest_cols:
                if col in rate_df.columns:
                    rate_df[col] = rate_df[col].fillna(0.0)
            
            logger.info(f"검거율 계산 완료")
            logger.info(f"rate_df 컬럼: {rate_df.columns.tolist()}")
            logger.info(f"검거율 샘플: {rate_df[['자치구'] + arrest_cols].head(3).to_dict('records')}")
            
            # 3. 지도 데이터 로드
            logger.info("지도 데이터 로드 시작...")
            geo_data_path = Path(__file__).parent / "data" / "kr-state.json"
            
            if not geo_data_path.exists():
                raise FileNotFoundError(f"지도 데이터 파일을 찾을 수 없습니다: {geo_data_path}")
            
            with open(geo_data_path, 'r', encoding='utf-8') as f:
                seoul_geo = json.load(f)
            
            logger.info(f"지도 데이터 로드 완료: {len(seoul_geo['features'])}개 자치구")
            
            # 4. 카카오맵 API 키 가져오기
            logger.info("카카오맵 API 키 가져오기...")
            kakao_api_key = None
            try:
                kakao_map = KakaoMapSingleton()
                kakao_api_key = kakao_map.get_api_key()
                logger.info("✅ 카카오맵 API 키 가져오기 성공")
            except Exception as e:
                logger.warning(f"⚠️ 카카오맵 API 키 가져오기 실패: {e}")
                kakao_api_key = None
            
            # 5. Folium 지도 생성
            logger.info("Folium 지도 생성 시작...")
            # 서울시청 좌표
            seoul_center = [37.5665, 126.9780]
            m = folium.Map(location=seoul_center, zoom_start=11, tiles='OpenStreetMap')
            
            # 범죄 유형별 Choropleth 레이어 추가
            # 히트맵과 동일하게 범죄 발생율 5가지만 사용 (총 범죄 발생율 제외)
            crime_rate_mapping = {
                '살인 발생율': '살인 발생율',
                '강도 발생율': '강도 발생율',
                '강간 발생율': '강간 발생율',
                '절도 발생율': '절도 발생율',
                '폭력 발생율': '폭력 발생율'
            }
            
            colors = {
                '살인 발생율': 'Reds',
                '강도 발생율': 'Oranges',
                '강간 발생율': 'Purples',
                '절도 발생율': 'Blues',
                '폭력 발생율': 'YlOrRd'
            }
            
            # 자치구별 데이터를 딕셔너리로 변환 (Popup/Tooltip용)
            district_data = {}
            for _, row in rate_df.iterrows():
                district = row['자치구']
                # 검거율 데이터도 포함
                district_row = merged_df[merged_df['자치구'] == district]
                
                # 검거율 값 확인 및 로깅
                arrest_rates = {
                    '살인 검거율': row.get('살인 검거율', 0),
                    '강도 검거율': row.get('강도 검거율', 0),
                    '강간 검거율': row.get('강간 검거율', 0),
                    '절도 검거율': row.get('절도 검거율', 0),
                    '폭력 검거율': row.get('폭력 검거율', 0),
                }
                
                # 첫 번째 자치구의 검거율 로깅 (디버깅용)
                if len(district_data) == 0:
                    logger.info(f"🔍 검거율 데이터 확인 - {district}: {arrest_rates}")
                    logger.info(f"   rate_df 컬럼: {rate_df.columns.tolist()}")
                    logger.info(f"   rate_df 샘플: {row.to_dict()}")
                
                district_data[district] = {
                    '살인 발생율': row.get('살인 발생율', 0),
                    '강도 발생율': row.get('강도 발생율', 0),
                    '강간 발생율': row.get('강간 발생율', 0),
                    '절도 발생율': row.get('절도 발생율', 0),
                    '폭력 발생율': row.get('폭력 발생율', 0),
                    '살인 검거율': arrest_rates['살인 검거율'],
                    '강도 검거율': arrest_rates['강도 검거율'],
                    '강간 검거율': arrest_rates['강간 검거율'],
                    '절도 검거율': arrest_rates['절도 검거율'],
                    '폭력 검거율': arrest_rates['폭력 검거율'],
                }
            
            # GeoJSON에 데이터 추가 (Popup/Tooltip용)
            for feature in seoul_geo['features']:
                district_name = feature['id']
                if district_name in district_data:
                    data = district_data[district_name]
                    # properties에 데이터 추가 (히트맵과 동일하게 범죄 발생율과 검거율만)
                    if 'properties' not in feature:
                        feature['properties'] = {}
                    feature['properties'].update({
                        '살인 발생율': data['살인 발생율'],
                        '강도 발생율': data['강도 발생율'],
                        '강간 발생율': data['강간 발생율'],
                        '절도 발생율': data['절도 발생율'],
                        '폭력 발생율': data['폭력 발생율'],
                    })
            
            # Popup/Tooltip용 별도 레이어 생성 (모든 범죄 유형에 공통으로 사용)
            # Choropleth는 색상만 표시하고, 별도 GeoJson 레이어로 Popup/Tooltip 추가
            # info_layer 제거 - Choropleth에 직접 Popup/Tooltip 추가
            label_layer = folium.FeatureGroup(name="자치구 수치 표시")
            
            # 각 자치구의 중심점 계산 및 수치 표시를 위한 함수
            def calculate_centroid(coordinates):
                """GeoJSON 좌표에서 중심점 계산"""
                if isinstance(coordinates[0][0], list):
                    # MultiPolygon 또는 Polygon with holes
                    all_coords = []
                    for coord_group in coordinates:
                        if isinstance(coord_group[0], list):
                            all_coords.extend(coord_group)
                        else:
                            all_coords.append(coord_group)
                    coords = all_coords
                else:
                    coords = coordinates
                
                lats = [coord[1] for coord in coords]
                lons = [coord[0] for coord in coords]
                return [sum(lats) / len(lats), sum(lons) / len(lons)]
            
            # Popup/Tooltip HTML 생성 함수
            def create_popup_tooltip(district_name, data):
                """Popup과 Tooltip HTML 생성"""
                tooltip_html = f"""
                <div>
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">
                        {district_name}
                    </div>
                    <div style="font-size: 12px;">
                        살인: {data['살인 발생율']:.4f} | 강도: {data['강도 발생율']:.4f} | 강간: {data['강간 발생율']:.4f} | 절도: {data['절도 발생율']:.4f} | 폭력: {data['폭력 발생율']:.4f}
                    </div>
                </div>
                """
                
                popup_html = f"""
                <div style="width: 320px; font-family: Arial, sans-serif;">
                    <h3 style="margin: 0 0 12px 0; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 8px; font-size: 18px;">
                        📍 {district_name}
                    </h3>
                    <div style="margin-top: 15px;">
                        <h4 style="margin: 0 0 10px 0; color: #34495e; font-size: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px;">
                            📊 범죄 발생율 (정규화: 최댓값=1)
                        </h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px;">
                            <tr style="background: linear-gradient(90deg, #fff3cd 0%, #ffeaa7 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔴 살인:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #c0392b;">{data['살인 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #ffeaa7 0%, #fdcb6e 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟠 강도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #d35400;">{data['강도 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #e1bee7 0%, #ce93d8 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟣 강간:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #7b1fa2;">{data['강간 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #bbdefb 0%, #90caf9 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔵 절도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1565c0;">{data['절도 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #ffccbc 0%, #ffab91 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟧 폭력:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #d84315;">{data['폭력 발생율']:.4f}</td>
                            </tr>
                        </table>
                        <h4 style="margin: 15px 0 10px 0; color: #34495e; font-size: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px;">
                            ✅ 범죄 검거율 (%)
                        </h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <tr style="background: linear-gradient(90deg, #c8e6c9 0%, #a5d6a7 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔴 살인:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('살인 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #a5d6a7 0%, #81c784 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟠 강도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('강도 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #81c784 0%, #66bb6a 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟣 강간:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('강간 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #66bb6a 0%, #4caf50 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔵 절도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('절도 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #4caf50 0%, #388e3c 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟧 폭력:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('폭력 검거율', 0):.1f}%</td>
                            </tr>
                        </table>
                    </div>
                </div>
                """
                return popup_html, tooltip_html
            
            # onEachFeature 콜백 함수 정의
            def on_each_feature(feature, layer):
                """Choropleth의 각 feature에 Popup과 Tooltip 추가"""
                district_name = feature.get('id')
                if district_name and district_name in district_data:
                    data = district_data[district_name]
                    popup_html, tooltip_html = create_popup_tooltip(district_name, data)
                    layer.bind_popup(folium.Popup(popup_html, max_width=300))
                    layer.bind_tooltip(folium.Tooltip(tooltip_html, sticky=True))
            
            # 각 자치구 중심에 수치 표시
            for feature in seoul_geo['features']:
                district_name = feature['id']
                if district_name in district_data:
                    data = district_data[district_name]
                    
                    # 중심점 계산
                    geometry = feature['geometry']
                    if geometry['type'] == 'Polygon':
                        coords = geometry['coordinates'][0]
                        centroid = calculate_centroid(coords)
                    elif geometry['type'] == 'MultiPolygon':
                        # 첫 번째 Polygon의 좌표 사용
                        coords = geometry['coordinates'][0][0]
                        centroid = calculate_centroid(coords)
                    else:
                        continue
                    
                    # 수치 레이블 HTML 생성
                    # 히트맵과 동일하게 각 항목별 검거율 표시
                    label_html = f"""
                    <div style="
                        background: rgba(255, 255, 255, 0.9);
                        border: 2px solid #3498db;
                        border-radius: 8px;
                        padding: 8px 12px;
                        font-family: Arial, sans-serif;
                        font-size: 10px;
                        font-weight: bold;
                        text-align: center;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                        min-width: 140px;
                    ">
                        <div style="color: #2c3e50; margin-bottom: 4px; font-size: 12px; font-weight: bold;">
                            {district_name}
                        </div>
                        <div style="color: #e74c3c; font-size: 10px; margin-bottom: 2px;">
                            살인: {data['살인 발생율']:.4f} | 강도: {data['강도 발생율']:.4f}
                        </div>
                        <div style="color: #e74c3c; font-size: 10px; margin-bottom: 2px;">
                            강간: {data['강간 발생율']:.4f} | 절도: {data['절도 발생율']:.4f} | 폭력: {data['폭력 발생율']:.4f}
                        </div>
                        <div style="color: #27ae60; font-size: 10px; margin-bottom: 2px;">
                            살인: {data.get('살인 검거율', 0):.1f}% | 강도: {data.get('강도 검거율', 0):.1f}%
                        </div>
                        <div style="color: #27ae60; font-size: 10px;">
                            강간: {data.get('강간 검거율', 0):.1f}% | 절도: {data.get('절도 검거율', 0):.1f}% | 폭력: {data.get('폭력 검거율', 0):.1f}%
                        </div>
                    </div>
                    """
                    
                    # DivIcon을 사용하여 텍스트 레이블 추가
                    icon = folium.DivIcon(
                        html=label_html,
                        icon_size=(150, 60),
                        icon_anchor=(75, 30)
                    )
                    
                    folium.Marker(
                        location=centroid,
                        icon=icon,
                        tooltip=f"{district_name} 클릭하여 상세 정보 보기"
                    ).add_to(label_layer)
            
            label_layer.add_to(m)
            logger.info("자치구 수치 표시 레이어 추가 완료")
            
            # Popup/Tooltip HTML 생성 함수
            def create_popup_tooltip(district_name, data):
                """Popup과 Tooltip HTML 생성"""
                tooltip_html = f"""
                <div>
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">
                        {district_name}
                    </div>
                    <div style="font-size: 12px;">
                        살인: {data['살인 발생율']:.4f} | 강도: {data['강도 발생율']:.4f} | 강간: {data['강간 발생율']:.4f} | 절도: {data['절도 발생율']:.4f} | 폭력: {data['폭력 발생율']:.4f}
                    </div>
                </div>
                """
                
                popup_html = f"""
                <div style="width: 320px; font-family: Arial, sans-serif;">
                    <h3 style="margin: 0 0 12px 0; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 8px; font-size: 18px;">
                        📍 {district_name}
                    </h3>
                    <div style="margin-top: 15px;">
                        <h4 style="margin: 0 0 10px 0; color: #34495e; font-size: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px;">
                            📊 범죄 발생율 (정규화: 최댓값=1)
                        </h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px;">
                            <tr style="background: linear-gradient(90deg, #fff3cd 0%, #ffeaa7 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔴 살인:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #c0392b;">{data['살인 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #ffeaa7 0%, #fdcb6e 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟠 강도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #d35400;">{data['강도 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #e1bee7 0%, #ce93d8 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟣 강간:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #7b1fa2;">{data['강간 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #bbdefb 0%, #90caf9 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔵 절도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1565c0;">{data['절도 발생율']:.4f}</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #ffccbc 0%, #ffab91 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟧 폭력:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #d84315;">{data['폭력 발생율']:.4f}</td>
                            </tr>
                        </table>
                        <h4 style="margin: 15px 0 10px 0; color: #34495e; font-size: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px;">
                            ✅ 범죄 검거율 (%)
                        </h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <tr style="background: linear-gradient(90deg, #c8e6c9 0%, #a5d6a7 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔴 살인:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('살인 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #a5d6a7 0%, #81c784 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟠 강도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('강도 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #81c784 0%, #66bb6a 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟣 강간:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('강간 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #66bb6a 0%, #4caf50 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🔵 절도:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('절도 검거율', 0):.1f}%</td>
                            </tr>
                            <tr style="background: linear-gradient(90deg, #4caf50 0%, #388e3c 100%);">
                                <td style="padding: 6px 8px; border: 1px solid #ddd; font-weight: bold;">🟧 폭력:</td>
                                <td style="padding: 6px 8px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #2e7d32;">{data.get('폭력 검거율', 0):.1f}%</td>
                            </tr>
                        </table>
                    </div>
                </div>
                """
                return popup_html, tooltip_html
            
            for rate_col, display_name in crime_rate_mapping.items():
                if rate_col in rate_df.columns:
                    # Choropleth 레이어 생성
                    choropleth = folium.Choropleth(
                        geo_data=seoul_geo,
                        name=display_name,
                        data=rate_df,
                        columns=['자치구', rate_col],
                        key_on='feature.id',
                        fill_color=colors.get(rate_col, 'YlOrRd'),
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name=f'{display_name} (10만명당)',
                    )
                    choropleth.add_to(m)
                    
                    # Choropleth의 내부 GeoJson 레이어에 Popup/Tooltip 추가
                    # geojson 속성은 FeatureGroup이므로 각 레이어에 접근
                    for feature in seoul_geo['features']:
                        district_name = feature.get('id')
                        if district_name and district_name in district_data:
                            data = district_data[district_name]
                            popup_html, tooltip_html = create_popup_tooltip(district_name, data)
                            
                            # Choropleth의 geojson FeatureGroup에서 해당 feature 찾기
                            # 각 레이어를 순회하며 feature id로 매칭
                            for layer in choropleth.geojson._children.values():
                                if hasattr(layer, 'feature') and layer.feature.get('id') == district_name:
                                    layer.bind_popup(folium.Popup(popup_html, max_width=300))
                                    layer.bind_tooltip(folium.Tooltip(tooltip_html, sticky=True))
                                    break
                    
                    logger.info(f"{display_name} 레이어 추가 완료 (Popup/Tooltip 포함)")
            
            # 레이어 컨트롤 추가
            folium.LayerControl().add_to(m)
            
            # 6. HTML 문자열 생성 및 카카오맵 JavaScript API 추가
            html_str = m.get_root().render()
            
            # 카카오맵 JavaScript API 추가 (HTML에 삽입)
            if kakao_api_key:
                # 카카오맵 JavaScript API 스크립트 추가
                kakao_script = f"""
                <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={kakao_api_key}"></script>
                <script>
                    // 카카오맵 API 로드 완료 후 지도 초기화
                    window.addEventListener('load', function() {{
                        console.log('카카오맵 API 로드 완료');
                        // 기존 Folium 지도 위에 카카오맵 레이어 추가 가능
                    }});
                </script>
                """
                # HTML의 </head> 태그 앞에 카카오맵 스크립트 추가
                html_str = html_str.replace('</head>', f'{kakao_script}</head>')
                logger.info("✅ 카카오맵 JavaScript API 스크립트 추가 완료")
            
            # 7. HTML 파일 저장 (save 폴더에 seoul_crime.html로 저장)
            html_save_path = save_path / 'seoul_crime.html'
            try:
                with open(html_save_path, 'w', encoding='utf-8') as f:
                    f.write(html_str)
                logger.info(f"✅ 지도 HTML 파일 저장 완료: {html_save_path}")
            except Exception as e:
                logger.error(f"❌ 지도 HTML 파일 저장 실패: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            logger.info("🗺️ 범죄율 지도 생성 완료 (범죄 발생율 + 검거율 포함)")
            
            return html_str
            
        except Exception as e:
            logger.error(f"범죄율 지도 생성 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
