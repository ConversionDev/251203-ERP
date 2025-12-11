"""
US Unemployment Service - 미국 실업률 데이터 시각화 서비스
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import requests
import pandas as pd
import folium

logger = logging.getLogger(__name__)


class USUnemploymentService:
    """미국 실업률 데이터 시각화 서비스 클래스"""
    
    def __init__(
        self,
        geo_data_url: str = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json",
        data_url: str = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_unemployment_oct_2012.csv",
        map_location: list = [48, -102],
        zoom_start: int = 3
    ):
        """
        초기화
        
        Args:
            geo_data_url: 지리 데이터 JSON URL
            data_url: 실업률 데이터 CSV URL
            map_location: 지도 중심 좌표 [위도, 경도]
            zoom_start: 초기 줌 레벨
        """
        self.geo_data_url = geo_data_url
        self.data_url = data_url
        self.map_location = map_location
        self.zoom_start = zoom_start
        
        self.state_geo: Optional[Dict[str, Any]] = None
        self.state_data: Optional[pd.DataFrame] = None
        self.map: Optional[folium.Map] = None
        
        logger.info("US Unemployment Service 초기화 완료")
    
    def load_geo_data(self) -> Dict[str, Any]:
        """
        지리 데이터 로드
        
        Returns:
            지리 데이터 JSON 딕셔너리
        """
        logger.info(f"지리 데이터 로드 시작: {self.geo_data_url}")
        try:
            response = requests.get(self.geo_data_url)
            response.raise_for_status()
            self.state_geo = response.json()
            logger.info("지리 데이터 로드 완료")
            return self.state_geo
        except requests.exceptions.RequestException as e:
            logger.error(f"지리 데이터 로드 실패: {e}")
            raise
    
    def load_unemployment_data(self) -> pd.DataFrame:
        """
        실업률 데이터 로드
        
        Returns:
            실업률 데이터 DataFrame
        """
        logger.info(f"실업률 데이터 로드 시작: {self.data_url}")
        try:
            self.state_data = pd.read_csv(self.data_url)
            logger.info(f"실업률 데이터 로드 완료: {self.state_data.shape}")
            return self.state_data
        except Exception as e:
            logger.error(f"실업률 데이터 로드 실패: {e}")
            raise
    
    def create_map(
        self,
        fill_color: str = "YlGn",
        fill_opacity: float = 0.7,
        line_opacity: float = 0.2,
        legend_name: str = "Unemployment Rate (%)"
    ) -> folium.Map:
        """
        실업률 지도 생성
        
        Args:
            fill_color: 채우기 색상 스키마
            fill_opacity: 채우기 투명도
            line_opacity: 선 투명도
            legend_name: 범례 이름
            
        Returns:
            생성된 Folium 지도 객체
        """
        logger.info("지도 생성 시작...")
        
        # 데이터 로드 (아직 로드되지 않은 경우)
        if self.state_geo is None:
            self.load_geo_data()
        if self.state_data is None:
            self.load_unemployment_data()
        
        # 지도 생성
        self.map = folium.Map(
            location=self.map_location,
            zoom_start=self.zoom_start
        )
        
        # Choropleth 레이어 추가
        folium.Choropleth(
            geo_data=self.state_geo,
            name="choropleth",
            data=self.state_data,
            columns=["State", "Unemployment"],
            key_on="feature.id",
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name,
        ).add_to(self.map)
        
        # 레이어 컨트롤 추가
        folium.LayerControl().add_to(self.map)
        
        logger.info("지도 생성 완료")
        return self.map
    
    def save_map(self, file_path: str | Path) -> str:
        """
        지도를 HTML 파일로 저장
        
        Args:
            file_path: 저장할 파일 경로
            
        Returns:
            저장된 파일 경로
        """
        if self.map is None:
            raise ValueError("지도가 생성되지 않았습니다. create_map()을 먼저 호출하세요.")
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"지도 저장 시작: {file_path}")
        self.map.save(str(file_path))
        logger.info(f"지도 저장 완료: {file_path}")
        
        return str(file_path)
    
    def get_map(self) -> Optional[folium.Map]:
        """
        생성된 지도 객체 반환
        
        Returns:
            Folium 지도 객체 (없으면 None)
        """
        return self.map
    
    def visualize(self, save_path: Optional[str | Path] = None) -> folium.Map:
        """
        데이터 로드, 지도 생성, 저장을 한 번에 수행
        
        Args:
            save_path: 저장할 파일 경로 (None이면 저장하지 않음)
            
        Returns:
            생성된 Folium 지도 객체
        """
        logger.info("🦝🦝 시각화 시작")
        
        # 지도 생성
        self.create_map()
        
        # 저장 (경로가 제공된 경우)
        if save_path:
            self.save_map(save_path)
        
        logger.info("🦝🦝 시각화 완료")
        return self.map