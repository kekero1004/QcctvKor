from typing import List, Dict, Optional, Callable
from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint,
                      QgsField, QgsProject, QgsPointXY, QgsSvgMarkerSymbolLayer,
                      QgsSingleSymbolRenderer, QgsSymbol, QgsPalLayerSettings,
                      QgsTextFormat, QgsVectorLayerSimpleLabeling, QgsVectorFileWriter)
from qgis.PyQt.QtCore import QVariant, QObject, pyqtSignal
from qgis.PyQt.QtGui import QColor
from ..utils.logger import Logger
from ..utils.exceptions import (
    QcctvKorError, ApiError, NetworkError, DataError,
    LayerError, ConfigError, handle_exception
)
import requests
import json
import os
import time
from threading import Thread
from functools import lru_cache
import csv
from datetime import datetime
from .filter_settings import FilterSettings
from QcctvKor.view.settings_dialog import SettingsDialog
from ..utils.config_manager import ConfigManager

logger = Logger.get_logger()

class CctvModel(QObject):
    # 시그널 정의
    data_loaded = pyqtSignal(bool)  # 데이터 로딩 완료 시그널
    loading_progress = pyqtSignal(int, int)  # 로딩 진행률 시그널
    
    def __init__(self):
        super().__init__()
        self.layer: Optional[QgsVectorLayer] = None
        self.cctv_data: List[Dict] = []
        self.filtered_data: List[Dict] = []
        self.layer_name = "QcctvKor_temp_layer"
        
        # API 설정 로드 (초기화 시에는 오류 발생하지 않음)
        try:
            config_manager = ConfigManager()
            self.api_key = config_manager.get_api_key()
            self.base_url = "http://openapi.its.go.kr:8081/api/NCCTVInfo"
            logger.info("API 설정이 로드되었습니다.")
        except Exception as e:
            logger.error(Logger.format_error(e, "API 설정 로드 실패"))
            self.api_key = ""
            self.base_url = "http://openapi.its.go.kr:8081/api/NCCTVInfo"
            
        self._cache = {}
        self._cache_timeout = 300
        self.filter_settings = FilterSettings()
        self.current_filter = None
    
    def load_cctv_data(self) -> None:
        """비동기적으로 CCTV 데이터 로드"""
        # API 키 검사는 여기서 수행
        if not self.api_key:
            raise ConfigError("API 키가 설정되지 않았습니다. '플러그인 > QcctvKor > ITS API 키 설정' 메뉴에서 API 키를 설정해주세요.")
        
        Thread(target=self._async_load_data, daemon=True).start()
        
    @Logger.log_function_call
    def _async_load_data(self) -> None:
        """비동기 데이터 로딩 처리"""
        try:
            # 캐시 확인
            cached_data = self._get_cached_data()
            if cached_data:
                logger.info("캐시된 데이터를 사용합니다.")
                self.cctv_data = cached_data
                self.data_loaded.emit(True)
                return
                
            # API 호출
            params = self._get_api_params()
            try:
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise NetworkError(f"API 호출 실패: {str(e)}")
                
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise DataError(f"JSON 파싱 실패: {str(e)}")
                
            if "response" not in data or "data" not in data["response"]:
                raise ApiError("잘못된 API 응답 형식")
                
            # 데이터 파싱
            self.cctv_data = []
            total_items = len(data["response"]["data"])
            logger.info(f"총 {total_items}개의 CCTV 데이터를 로드합니다.")
            
            for i, cctv in enumerate(data["response"]["data"]):
                try:
                    self.cctv_data.append(self._parse_cctv_data(cctv))
                    self.loading_progress.emit(i + 1, total_items)
                except (ValueError, KeyError) as e:
                    logger.warning(f"잘못된 CCTV 데이터 무시: {str(e)}")
                    continue
                    
            # 캐시 업데이트
            self._update_cache(self.cctv_data)
            logger.info(f"{len(self.cctv_data)}개의 CCTV 데이터가 로드되었습니다.")
            
            if not self.cctv_data:
                raise DataError("유효한 CCTV 데이터가 없습니다.")
                
            self.data_loaded.emit(True)
            
        except Exception as e:
            logger.error(Logger.format_error(e, "데이터 로딩 실패"))
            self.data_loaded.emit(False)
            raise handle_exception(e)
            
    @lru_cache(maxsize=100)
    def get_cctv_info(self, feature_id: int) -> Dict:
        """캐시된 CCTV 정보 조회"""
        if not self.layer:
            raise Exception("Layer not initialized")
            
        feature = next(self.layer.getFeatures(f"$id = {feature_id}"), None)
        if not feature:
            raise Exception(f"Feature {feature_id} not found")
            
        return {
            "name": feature["name"],
            "url": feature["url"],
            "geometry": feature.geometry().asPoint()
        }
        
    def _get_cached_data(self) -> Optional[List[Dict]]:
        """캐시된 데이터 조회"""
        if not self._cache:
            return None
            
        cache_time = self._cache.get("timestamp", 0)
        if time.time() - cache_time > self._cache_timeout:
            return None
            
        return self._cache.get("data")
        
    def _update_cache(self, data: List[Dict]) -> None:
        """캐시 업데이트"""
        self._cache = {
            "timestamp": time.time(),
            "data": data
        }
        
    def _get_api_params(self) -> Dict:
        """API 파라미터 생성"""
        return {
            "key": self.api_key,
            "type": "json",
            "cctvType": "1",
            "minX": "126.5",
            "maxX": "127.5",
            "minY": "37.0",
            "maxY": "38.0",
            "getType": "json"
        }
        
    def _parse_cctv_data(self, cctv: Dict) -> Dict:
        """CCTV 데이터 파싱"""
        return {
            "name": cctv.get("cctvName", "Unknown"),
            "url": cctv.get("cctvUrl", ""),
            "lat": float(cctv.get("coordY", 0)),
            "lon": float(cctv.get("coordX", 0))
        }
    
    def _load_sample_data(self) -> None:
        """Load sample CCTV data for testing"""
        self.cctv_data = [
            {
                "name": "서울 강남대로",
                "url": "rtsp://example.com/stream1",
                "lat": 37.5665,
                "lon": 126.9780
            },
            {
                "name": "서울 테헤란로",
                "url": "rtsp://example.com/stream2",
                "lat": 37.5701,
                "lon": 126.9827
            }
        ]
    
    @Logger.log_function_call
    def create_temp_layer(self) -> QgsVectorLayer:
        """Create temporary vector layer for CCTV points"""
        try:
            # Create layer
            self.layer = QgsVectorLayer("Point?crs=EPSG:4326", self.layer_name, "memory")
            if not self.layer.isValid():
                raise LayerError("임시 레이어 생성 실패")
                
            # Add fields
            provider = self.layer.dataProvider()
            provider.addAttributes([
                QgsField("name", QVariant.String),
                QgsField("url", QVariant.String)
            ])
            self.layer.updateFields()
            
            # Set styling
            self._set_layer_style()
            self._setup_labels()
            
            # Add to project
            QgsProject.instance().addMapLayer(self.layer)
            logger.info("임시 레이어가 생성되었습니다.")
            return self.layer
            
        except Exception as e:
            logger.error(Logger.format_error(e, "레이어 생성 실패"))
            raise handle_exception(e)
            
    def _set_layer_style(self) -> None:
        """Set the layer symbol style"""
        # Create SVG marker symbol
        svg_path = os.path.join(os.path.dirname(__file__), "..", "resources", "cctv_icon.svg")
        if os.path.exists(svg_path):
            symbol_layer = QgsSvgMarkerSymbolLayer(svg_path)
        else:
            # Fallback to simple circle marker if SVG not found
            symbol = QgsSymbol.defaultSymbol(self.layer.geometryType())
            symbol.setColor(QColor(255, 0, 0))  # Red color
            symbol.setSize(4)
            renderer = QgsSingleSymbolRenderer(symbol)
            self.layer.setRenderer(renderer)
            return
            
        # Configure symbol
        symbol_layer.setSize(6)  # Symbol size
        symbol_layer.setFillColor(QColor(255, 0, 0))  # Red fill
        symbol_layer.setStrokeColor(QColor(0, 0, 0))  # Black outline
        symbol_layer.setStrokeWidth(0.5)
        
        # Create and set renderer
        symbol = QgsSymbol.defaultSymbol(self.layer.geometryType())
        symbol.changeSymbolLayer(0, symbol_layer)
        renderer = QgsSingleSymbolRenderer(symbol)
        self.layer.setRenderer(renderer)
    
    def _setup_labels(self) -> None:
        """Setup layer labeling"""
        label_settings = QgsPalLayerSettings()
        text_format = QgsTextFormat()
        
        # Configure text format
        text_format.setSize(8)
        text_format.setColor(QColor(0, 0, 0))  # Black text
        
        # Configure label settings
        label_settings.setFormat(text_format)
        label_settings.fieldName = "name"  # Label using the name field
        label_settings.placement = QgsPalLayerSettings.OverPoint
        label_settings.quadOffset = QgsPalLayerSettings.QuadrantAboveRight
        label_settings.yOffset = 3
        
        # Apply labeling to layer
        self.layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        self.layer.setLabelsEnabled(True)
    
    def add_cctv_feature(self, name: str, url: str, lat: float, lon: float) -> None:
        """Add a CCTV feature to the layer"""
        if not self.layer:
            raise Exception("Layer not initialized")
            
        feature = QgsFeature()
        point = QgsPointXY(lon, lat)
        feature.setGeometry(QgsGeometry.fromPointXY(point))
        feature.setAttributes([name, url])
        
        self.layer.dataProvider().addFeature(feature)
        self.layer.updateExtents()
        self.layer.triggerRepaint()
    
    def remove_temp_layer(self) -> None:
        """Remove temporary CCTV layer"""
        if self.layer:
            QgsProject.instance().removeMapLayer(self.layer.id())
            self.layer = None
    
    def filter_cctv_data(self, region: str = None, road_type: str = None) -> None:
        """Filter CCTV data based on region and road type"""
        self.filtered_data = self.cctv_data.copy()
        
        if region:
            self.filtered_data = [
                cctv for cctv in self.filtered_data
                if region.lower() in cctv["name"].lower()
            ]
            
        if road_type:
            self.filtered_data = [
                cctv for cctv in self.filtered_data
                if road_type.lower() in cctv["name"].lower()
            ]
            
        # 필터링된 데이터로 레이어 업데이트
        self.update_layer_features()
        
    def update_layer_features(self) -> None:
        """Update layer with filtered features"""
        if not self.layer:
            return
            
        # 기존 피처 모두 제거
        self.layer.dataProvider().deleteFeatures(
            [f.id() for f in self.layer.getFeatures()]
        )
        
        # 필터링된 데이터로 피처 추가
        for cctv in (self.filtered_data or self.cctv_data):
            self.add_cctv_feature(
                cctv["name"],
                cctv["url"],
                cctv["lat"],
                cctv["lon"]
            )
            
    def search_cctv(self, keyword: str) -> List[Dict]:
        """Search CCTV by name"""
        if not keyword:
            return self.cctv_data
            
        return [
            cctv for cctv in self.cctv_data
            if keyword.lower() in cctv["name"].lower()
        ] 
    
    def save_filtered_results(self, file_path: str) -> None:
        """Save filtered CCTV data to CSV file"""
        try:
            data_to_save = self.filtered_data if self.filtered_data else self.cctv_data
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['name', 'url', 'lat', 'lon'])
                writer.writeheader()
                writer.writerows(data_to_save)
                
        except Exception as e:
            raise Exception(f"Failed to save results: {str(e)}")
            
    def load_saved_results(self, file_path: str) -> None:
        """Load saved CCTV data from CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.filtered_data = []
                
                for row in reader:
                    self.filtered_data.append({
                        'name': row['name'],
                        'url': row['url'],
                        'lat': float(row['lat']),
                        'lon': float(row['lon'])
                    })
                    
            # Update layer with loaded data
            self.update_layer_features()
            
        except Exception as e:
            raise Exception(f"Failed to load results: {str(e)}")
            
    def export_to_shapefile(self, file_path: str) -> None:
        """Export CCTV data to shapefile"""
        try:
            if not self.layer:
                raise Exception("Layer not initialized")
                
            # Create options for the save operation
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "ESRI Shapefile"
            options.fileEncoding = "UTF-8"
            
            # Save the layer
            error = QgsVectorFileWriter.writeAsVectorFormat(
                self.layer,
                file_path,
                "UTF-8",
                self.layer.crs(),
                "ESRI Shapefile"
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                raise Exception(f"Failed to save shapefile: {error[1]}")
                
        except Exception as e:
            raise Exception(f"Failed to export data: {str(e)}")
            
    def generate_report(self, file_path: str) -> None:
        """Generate report of CCTV data"""
        try:
            data_to_report = self.filtered_data if self.filtered_data else self.cctv_data
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("QcctvKor CCTV 데이터 보고서\n")
                f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"총 CCTV 수: {len(data_to_report)}\n")
                
                # 지역별 통계
                regions = {}
                for cctv in data_to_report:
                    region = cctv['name'].split()[0]  # 첫 번째 단어를 지역으로 가정
                    regions[region] = regions.get(region, 0) + 1
                    
                f.write("\n지역별 CCTV 수:\n")
                for region, count in regions.items():
                    f.write(f"- {region}: {count}대\n")
                    
                # CCTV 목록
                f.write("\nCCTV 목록:\n")
                for cctv in data_to_report:
                    f.write(f"- {cctv['name']} (위도: {cctv['lat']}, 경도: {cctv['lon']})\n")
                    
        except Exception as e:
            raise Exception(f"Failed to generate report: {str(e)}")
            
    def apply_filter(self, filter_config: Dict) -> None:
        """Apply filter configuration"""
        try:
            self.current_filter = filter_config
            region = filter_config.get("region")
            road_type = filter_config.get("road_type")
            keyword = filter_config.get("keyword")
            
            # 필터링 적용
            self.filtered_data = self.cctv_data.copy()
            
            if region and region != "전체":
                self.filtered_data = [
                    cctv for cctv in self.filtered_data
                    if region.lower() in cctv["name"].lower()
                ]
                
            if road_type and road_type != "전체":
                self.filtered_data = [
                    cctv for cctv in self.filtered_data
                    if road_type.lower() in cctv["name"].lower()
                ]
                
            if keyword:
                self.filtered_data = [
                    cctv for cctv in self.filtered_data
                    if keyword.lower() in cctv["name"].lower()
                ]
                
            # 레이어 업데이트
            self.update_layer_features()
            logger.info(
                f"필터 적용됨 (지역: {region}, 도로: {road_type}, "
                f"키워드: {keyword}) - {len(self.filtered_data)}개 결과"
            )
            
        except Exception as e:
            logger.error(Logger.format_error(e, "필터 적용 실패"))
            raise handle_exception(e)
            
    def get_current_filter(self) -> Optional[Dict]:
        """Get current filter configuration"""
        return self.current_filter
        
    def clear_filter(self) -> None:
        """Clear current filter"""
        self.current_filter = None
        self.filtered_data = []
        self.update_layer_features()
        logger.info("필터가 초기화되었습니다.")
        
    def get_filter_stats(self) -> Dict:
        """Get filter statistics"""
        data = self.filtered_data if self.filtered_data else self.cctv_data
        
        # 지역별 통계
        regions = {}
        road_types = {}
        
        for cctv in data:
            name_parts = cctv["name"].split()
            if name_parts:
                region = name_parts[0]
                regions[region] = regions.get(region, 0) + 1
                
                # 도로 유형 분류
                for road in ["고속도로", "국도", "시도"]:
                    if road in cctv["name"]:
                        road_types[road] = road_types.get(road, 0) + 1
                        break
                        
        return {
            "total": len(data),
            "regions": regions,
            "road_types": road_types,
            "has_filter": bool(self.current_filter)
        }

# 다음 코드 블록은 테스트용으로 남겨두었습니다.
# 실제 사용 시에는 이 코드를 제거하세요.
#if __name__ == "__main__":
#    dialog = SettingsDialog()
#    dialog.exec_() 