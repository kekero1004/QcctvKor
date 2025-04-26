from typing import Dict, List, Optional
from qgis.PyQt.QtCore import QSettings
import json
from datetime import datetime
from ..utils.logger import Logger
from ..utils.exceptions import ConfigError

logger = Logger.get_logger()

class FilterSettings:
    def __init__(self):
        self.settings = QSettings("QcctvKor", "QcctvKor")
        
    def save_filter(self, name: str, filter_config: Dict) -> None:
        """Save filter configuration"""
        try:
            # 기존 필터 목록 로드
            filters = self.get_saved_filters()
            
            # 새 필터 추가
            filters[name] = {
                "config": filter_config,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
            
            # 설정 저장
            self.settings.setValue("saved_filters", json.dumps(filters))
            logger.info(f"필터 '{name}' 저장됨")
            
        except Exception as e:
            logger.error(f"필터 저장 실패: {str(e)}")
            raise ConfigError(f"필터 저장 실패: {str(e)}")
            
    def load_filter(self, name: str) -> Optional[Dict]:
        """Load saved filter configuration"""
        try:
            filters = self.get_saved_filters()
            if name not in filters:
                return None
                
            # 마지막 사용 시간 업데이트
            filters[name]["last_used"] = datetime.now().isoformat()
            self.settings.setValue("saved_filters", json.dumps(filters))
            
            return filters[name]["config"]
            
        except Exception as e:
            logger.error(f"필터 로드 실패: {str(e)}")
            raise ConfigError(f"필터 로드 실패: {str(e)}")
            
    def get_saved_filters(self) -> Dict:
        """Get all saved filters"""
        try:
            filters_json = self.settings.value("saved_filters", "{}")
            return json.loads(filters_json)
        except Exception as e:
            logger.error(f"필터 목록 로드 실패: {str(e)}")
            return {}
            
    def delete_filter(self, name: str) -> bool:
        """Delete saved filter"""
        try:
            filters = self.get_saved_filters()
            if name in filters:
                del filters[name]
                self.settings.setValue("saved_filters", json.dumps(filters))
                logger.info(f"필터 '{name}' 삭제됨")
                return True
            return False
            
        except Exception as e:
            logger.error(f"필터 삭제 실패: {str(e)}")
            raise ConfigError(f"필터 삭제 실패: {str(e)}")
            
    def get_filter_info(self, name: str) -> Optional[Dict]:
        """Get filter metadata"""
        filters = self.get_saved_filters()
        return filters.get(name)
        
    def get_recent_filters(self, limit: int = 5) -> List[str]:
        """Get recently used filters"""
        filters = self.get_saved_filters()
        sorted_filters = sorted(
            filters.items(),
            key=lambda x: x[1]["last_used"],
            reverse=True
        )
        return [f[0] for f in sorted_filters[:limit]] 