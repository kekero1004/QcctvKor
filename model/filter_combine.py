from typing import Dict, List, Optional
from qgis.PyQt.QtCore import QSettings
import json
from datetime import datetime
from ..utils.logger import Logger
from ..utils.exceptions import ConfigError

logger = Logger.get_logger()

class FilterCombine:
    def __init__(self):
        self.settings = QSettings("QcctvKor", "QcctvKor")
        
    def save_combined_filter(self, name: str, filters: List[Dict],
                           operator: str = "AND") -> None:
        """Save combined filter configuration"""
        try:
            combined_filters = self._get_combined_filters()
            
            # 새 조합 필터 추가
            combined_filters[name] = {
                "filters": filters,
                "operator": operator,
                "created_at": datetime.now().isoformat()
            }
            
            self.settings.setValue("combined_filters", json.dumps(combined_filters))
            logger.info(f"조합 필터 '{name}' 저장됨")
            
        except Exception as e:
            logger.error(f"조합 필터 저장 실패: {str(e)}")
            raise ConfigError(f"조합 필터 저장 실패: {str(e)}")
            
    def get_combined_filter(self, name: str) -> Optional[Dict]:
        """Get combined filter by name"""
        try:
            combined_filters = self._get_combined_filters()
            return combined_filters.get(name)
        except Exception as e:
            logger.error(f"조합 필터 로드 실패: {str(e)}")
            return None
            
    def get_all_combined_filters(self) -> Dict:
        """Get all combined filters"""
        return self._get_combined_filters()
        
    def delete_combined_filter(self, name: str) -> bool:
        """Delete combined filter by name"""
        try:
            combined_filters = self._get_combined_filters()
            if name in combined_filters:
                del combined_filters[name]
                self.settings.setValue("combined_filters",
                                    json.dumps(combined_filters))
                logger.info(f"조합 필터 '{name}' 삭제됨")
                return True
            return False
        except Exception as e:
            logger.error(f"조합 필터 삭제 실패: {str(e)}")
            return False
            
    def apply_combined_filter(self, name: str, data: List[Dict]) -> List[Dict]:
        """Apply combined filter to data"""
        try:
            combined_filter = self.get_combined_filter(name)
            if not combined_filter:
                raise ConfigError(f"조합 필터 '{name}'을(를) 찾을 수 없습니다.")
                
            filters = combined_filter["filters"]
            operator = combined_filter["operator"]
            
            filtered_data = data
            
            if operator == "AND":
                # 모든 필터 조건을 만족하는 데이터만 선택
                for filter_config in filters:
                    filtered_data = self._apply_single_filter(filter_config,
                                                           filtered_data)
            else:  # OR
                # 하나라도 만족하는 데이터 선택
                result_set = set()
                for filter_config in filters:
                    filtered = self._apply_single_filter(filter_config, data)
                    result_set.update(self._get_data_ids(filtered))
                    
                filtered_data = [item for item in data 
                               if self._get_item_id(item) in result_set]
                
            return filtered_data
            
        except Exception as e:
            logger.error(f"조합 필터 적용 실패: {str(e)}")
            raise ConfigError(f"조합 필터 적용 실패: {str(e)}")
            
    def _get_combined_filters(self) -> Dict:
        """Get all combined filters from settings"""
        try:
            filters_json = self.settings.value("combined_filters", "{}")
            return json.loads(filters_json)
        except Exception as e:
            logger.error(f"조합 필터 목록 로드 실패: {str(e)}")
            return {}
            
    def _apply_single_filter(self, filter_config: Dict,
                           data: List[Dict]) -> List[Dict]:
        """Apply single filter configuration to data"""
        region = filter_config.get("region", "")
        road_type = filter_config.get("road_type", "")
        keyword = filter_config.get("keyword", "").lower()
        
        filtered = data
        
        # 지역 필터링
        if region and region != "전체":
            filtered = [item for item in filtered 
                       if item.get("region") == region]
            
        # 도로 유형 필터링
        if road_type and road_type != "전체":
            filtered = [item for item in filtered 
                       if item.get("road_type") == road_type]
            
        # 키워드 필터링
        if keyword:
            filtered = [item for item in filtered 
                       if keyword in str(item).lower()]
            
        return filtered
        
    def _get_data_ids(self, data: List[Dict]) -> set:
        """Get set of data item IDs"""
        return {self._get_item_id(item) for item in data}
        
    def _get_item_id(self, item: Dict) -> str:
        """Get unique identifier for data item"""
        # CCTV 데이터의 고유 식별자 생성
        return f"{item.get('id', '')}_{item.get('location', '')}" 