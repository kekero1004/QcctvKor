from typing import Dict, List, Optional
from qgis.PyQt.QtCore import QSettings
import json
from datetime import datetime
from ..utils.logger import Logger
from ..utils.exceptions import ConfigError

logger = Logger.get_logger()

class FilterAuto:
    def __init__(self):
        self.settings = QSettings("QcctvKor", "QcctvKor")
        
    def save_auto_filter(self, filter_config: Dict, schedule: Dict) -> None:
        """Save automatic filter configuration"""
        try:
            auto_filters = self._get_auto_filters()
            
            # 새 자동 필터 추가
            auto_filters[filter_config["name"]] = {
                "config": filter_config,
                "schedule": schedule,
                "created_at": datetime.now().isoformat(),
                "last_run": None
            }
            
            self.settings.setValue("auto_filters", json.dumps(auto_filters))
            logger.info(f"자동 필터 '{filter_config['name']}' 저장됨")
            
        except Exception as e:
            logger.error(f"자동 필터 저장 실패: {str(e)}")
            raise ConfigError(f"자동 필터 저장 실패: {str(e)}")
            
    def get_due_filters(self) -> List[Dict]:
        """Get filters that are due to run"""
        try:
            auto_filters = self._get_auto_filters()
            due_filters = []
            now = datetime.now()
            
            for name, filter_data in auto_filters.items():
                schedule = filter_data["schedule"]
                last_run = filter_data.get("last_run")
                
                if last_run:
                    last_run = datetime.fromisoformat(last_run)
                    
                # 스케줄 확인
                if self._is_filter_due(schedule, last_run, now):
                    due_filters.append({
                        "name": name,
                        "config": filter_data["config"]
                    })
                    
            return due_filters
            
        except Exception as e:
            logger.error(f"자동 필터 확인 실패: {str(e)}")
            return []
            
    def update_last_run(self, filter_name: str) -> None:
        """Update last run time for a filter"""
        try:
            auto_filters = self._get_auto_filters()
            if filter_name in auto_filters:
                auto_filters[filter_name]["last_run"] = datetime.now().isoformat()
                self.settings.setValue("auto_filters", json.dumps(auto_filters))
                
        except Exception as e:
            logger.error(f"필터 실행 시간 업데이트 실패: {str(e)}")
            
    def _get_auto_filters(self) -> Dict:
        """Get all automatic filters"""
        try:
            filters_json = self.settings.value("auto_filters", "{}")
            return json.loads(filters_json)
        except Exception as e:
            logger.error(f"자동 필터 목록 로드 실패: {str(e)}")
            return {}
            
    def _is_filter_due(self, schedule: Dict, last_run: Optional[datetime],
                      current_time: datetime) -> bool:
        """Check if filter is due to run"""
        # 처음 실행하는 경우
        if not last_run:
            return True
            
        interval = schedule.get("interval", 0)  # 간격(분)
        days = schedule.get("days", [])  # 요일 (0-6, 0=월요일)
        times = schedule.get("times", [])  # 시간 (HH:MM)
        
        # 간격 기반 실행
        if interval > 0:
            minutes_passed = (current_time - last_run).total_seconds() / 60
            return minutes_passed >= interval
            
        # 요일 및 시간 기반 실행
        current_day = current_time.weekday()
        current_time_str = current_time.strftime("%H:%M")
        
        if days and current_day not in days:
            return False
            
        if times and current_time_str not in times:
            return False
            
        # 마지막 실행이 하루 이상 지났거나, 지정된 시간이 되었을 때
        return (current_time - last_run).days > 0 or current_time_str in times 