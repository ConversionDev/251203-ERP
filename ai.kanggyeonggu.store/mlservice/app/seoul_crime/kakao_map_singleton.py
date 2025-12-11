import os
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class KakaoMapSingleton:
    """카카오맵 API 싱글톤 클래스"""
    
    _instance = None  # 싱글턴 인스턴스를 저장할 클래스 변수
    _env_loaded = False

    def __new__(cls):
        """싱글톤 인스턴스 생성"""
        if cls._instance is None:  # 인스턴스가 없으면 생성
            cls._instance = super(KakaoMapSingleton, cls).__new__(cls)
            cls._instance._api_key = cls._instance._retrieve_api_key()  # API 키 가져오기
            cls._instance._base_url = "https://dapi.kakao.com/v2/local"
        return cls._instance  # 기존 인스턴스 반환

    def _retrieve_api_key(self):
        """루트 .env 파일에서 API 키 가져오기"""
        # .env 파일을 한 번만 로드
        if not KakaoMapSingleton._env_loaded:
            # 프로젝트 루트 경로 찾기 (현재 파일에서 상위로 올라가서 .env 파일 찾기)
            current_file = Path(__file__).resolve()
            root_path = current_file.parent
            
            # 루트 디렉토리까지 올라가면서 .env 파일 찾기
            while root_path != root_path.parent:
                env_path = root_path / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                    break
                root_path = root_path.parent
            
            KakaoMapSingleton._env_loaded = True
        
        # 환경 변수에서 API 키 가져오기 (KAKAO_REST_API_KEY 또는 KAKAO_MAP_API_KEY 지원)
        api_key = os.getenv("KAKAO_REST_API_KEY") or os.getenv("KAKAO_MAP_API_KEY")
        if not api_key:
            raise ValueError("KAKAO_REST_API_KEY 또는 KAKAO_MAP_API_KEY 환경변수가 설정되지 않았습니다.")
        return api_key

    def get_api_key(self):
        """저장된 API 키 반환"""
        return self._api_key

    def geocode(self, address, language='ko'):
        """주소를 위도, 경도로 변환하는 메서드 (카카오 맵 API)"""
        # 키워드 검색 API 사용 (장소명 검색용)
        url = f"{self._base_url}/search/keyword.json"
        headers = {
            "Authorization": f"KakaoAK {self._api_key}"
        }
        params = {
            "query": address
        }
        
        logger.info(f"🔍 카카오 맵 API 호출 시작: {address}")
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # 에러 응답 처리
            if response.status_code == 403:
                error_msg = response.json().get('message', 'Forbidden')
                logger.error(f"카카오 맵 API 403 에러: {error_msg}")
                logger.error(f"요청 URL: {url}")
                logger.error(f"요청 주소: {address}")
                raise ValueError(f"카카오 맵 API 접근 거부 (403): {error_msg}. 카카오 개발자 콘솔에서 '로컬' API가 활성화되어 있는지 확인하세요.")
            
            response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
            
            result = response.json()
            
            # Google Maps API와 유사한 형식으로 변환
            if result.get('documents') and len(result['documents']) > 0:
                doc = result['documents'][0]
                # 키워드 검색 결과는 place_name, address_name, road_address_name 등을 포함
                address_name = doc.get('address_name', '') or doc.get('road_address_name', '')
                lat = float(doc.get('y', 0))
                lng = float(doc.get('x', 0))
                logger.info(f"✅ 카카오 맵 API 성공: {address} → {address_name} (위도: {lat}, 경도: {lng})")
                return [{
                    "formatted_address": address_name,
                    "geometry": {
                        "location": {
                            "lat": lat,
                            "lng": lng
                        }
                    }
                }]
            logger.warning(f"⚠️ 카카오 맵 API 결과 없음: {address}")
            return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"카카오 맵 API 요청 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"카카오 맵 API 처리 오류: {e}")
            return []

    def _parse_address_components(self, doc):
        """
        카카오맵 API 결과를 구글맵 형식의 address_components로 변환
        
        Args:
            doc: 카카오맵 API 문서 객체
            
        Returns:
            address_components 리스트
        """
        components = []
        address_name = doc.get("address_name", "")
        
        if not address_name:
            return components
        
        parts = address_name.split()
        for part in parts:
            if part.endswith("구"):
                components.append({
                    "long_name": part,
                    "short_name": part,
                    "types": ["sublocality_level_1", "administrative_area_level_2"]
                })
            elif part.endswith("시") or part.endswith("도"):
                components.append({
                    "long_name": part,
                    "short_name": part,
                    "types": ["administrative_area_level_1"]
                })
        
        return components

