from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from qgis.PyQt.QtCore import QSettings
import json
from ..utils.logger import Logger
from ..utils.exceptions import ConfigError

logger = Logger.get_logger()

class FilterRecommend:
    def __init__(self):
        self.settings = QSettings("QcctvKor", "QcctvKor")
        
    def save_filter_usage(self, filter_config: Dict) -> None:
        """Save filter usage history"""
        try:
            usage_history = self._get_usage_history()
            
            # 필터 설정을 문자열로 변환
            filter_key = self._get_filter_key(filter_config)
            
            # 사용 기록 추가
            usage_history.append({
                "filter": filter_key,
                "timestamp": datetime.now().isoformat()
            })
            
            # 최근 100개 기록만 유지
            if len(usage_history) > 100:
                usage_history = usage_history[-100:]
                
            self.settings.setValue("filter_usage", json.dumps(usage_history))
            logger.info(f"필터 사용 기록 저장됨: {filter_key}")
            
        except Exception as e:
            logger.error(f"필터 사용 기록 저장 실패: {str(e)}")
            
    def get_recommendations(self, current_filter: Dict,
                          max_recommendations: int = 5) -> List[Dict]:
        """Get filter recommendations based on usage history"""
        try:
            recommendations = []
            
            # 시간대별 추천
            time_based = self._get_time_based_recommendations(max_recommendations)
            recommendations.extend(time_based)
            
            # 유사 필터 추천
            similar = self._get_similar_filters(current_filter,
                                             max_recommendations)
            recommendations.extend(similar)
            
            # 인기 필터 추천
            popular = self._get_popular_filters(max_recommendations)
            recommendations.extend(popular)
            
            # 중복 제거 및 최대 개수 제한
            unique_recommendations = []
            seen = set()
            
            for rec in recommendations:
                filter_key = self._get_filter_key(rec["filter"])
                if filter_key not in seen and len(unique_recommendations) < max_recommendations:
                    seen.add(filter_key)
                    unique_recommendations.append(rec)
                    
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"필터 추천 생성 실패: {str(e)}")
            return []
            
    def _get_usage_history(self) -> List[Dict]:
        """Get filter usage history"""
        try:
            history_json = self.settings.value("filter_usage", "[]")
            return json.loads(history_json)
        except Exception as e:
            logger.error(f"필터 사용 기록 로드 실패: {str(e)}")
            return []
            
    def _get_filter_key(self, filter_config: Dict) -> str:
        """Convert filter configuration to string key"""
        return json.dumps({
            "region": filter_config.get("region", ""),
            "road_type": filter_config.get("road_type", ""),
            "keyword": filter_config.get("keyword", "")
        }, sort_keys=True)
        
    def _parse_filter_key(self, filter_key: str) -> Dict:
        """Convert filter key back to configuration"""
        return json.loads(filter_key)
        
    def _get_time_based_recommendations(self,
                                      max_count: int) -> List[Dict]:
        """Get recommendations based on time patterns"""
        try:
            history = self._get_usage_history()
            current_hour = datetime.now().hour
            
            # 현재 시간대의 필터 사용 패턴 분석
            time_patterns = defaultdict(int)
            for entry in history:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp.hour == current_hour:
                    time_patterns[entry["filter"]] += 1
                    
            # 가장 많이 사용된 필터 선택
            recommendations = []
            for filter_key, count in sorted(time_patterns.items(),
                                         key=lambda x: x[1],
                                         reverse=True)[:max_count]:
                recommendations.append({
                    "filter": self._parse_filter_key(filter_key),
                    "reason": f"이 시간대에 자주 사용된 필터입니다.",
                    "confidence": min(count / 10, 1.0)  # 최대 1.0
                })
                
            return recommendations
            
        except Exception as e:
            logger.error(f"시간 기반 추천 생성 실패: {str(e)}")
            return []
            
    def _get_similar_filters(self, current_filter: Dict,
                           max_count: int) -> List[Dict]:
        """Get recommendations based on similarity to current filter"""
        try:
            history = self._get_usage_history()
            current_key = self._get_filter_key(current_filter)
            
            # 유사도 계산
            similarities = []
            for entry in history:
                filter_config = self._parse_filter_key(entry["filter"])
                similarity = self._calculate_similarity(current_filter,
                                                     filter_config)
                if similarity > 0:
                    similarities.append((entry["filter"], similarity))
                    
            # 가장 유사한 필터 선택
            recommendations = []
            for filter_key, similarity in sorted(similarities,
                                              key=lambda x: x[1],
                                              reverse=True)[:max_count]:
                if filter_key != current_key:
                    recommendations.append({
                        "filter": self._parse_filter_key(filter_key),
                        "reason": f"현재 필터와 유사한 설정입니다.",
                        "confidence": similarity
                    })
                    
            return recommendations
            
        except Exception as e:
            logger.error(f"유사 필터 추천 생성 실패: {str(e)}")
            return []
            
    def _get_popular_filters(self, max_count: int) -> List[Dict]:
        """Get recommendations based on overall popularity"""
        try:
            history = self._get_usage_history()
            
            # 최근 일주일 동안의 사용 빈도 계산
            week_ago = datetime.now() - timedelta(days=7)
            usage_count = Counter()
            
            for entry in history:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp > week_ago:
                    usage_count[entry["filter"]] += 1
                    
            # 가장 많이 사용된 필터 선택
            total_uses = sum(usage_count.values()) or 1
            recommendations = []
            
            for filter_key, count in usage_count.most_common(max_count):
                recommendations.append({
                    "filter": self._parse_filter_key(filter_key),
                    "reason": f"최근 일주일간 자주 사용된 필터입니다.",
                    "confidence": count / total_uses
                })
                
            return recommendations
            
        except Exception as e:
            logger.error(f"인기 필터 추천 생성 실패: {str(e)}")
            return []
            
    def _calculate_similarity(self, filter1: Dict, filter2: Dict) -> float:
        """Calculate similarity between two filters"""
        score = 0.0
        total_weight = 0.0
        
        # 지역 비교 (가중치: 0.4)
        if filter1.get("region") == filter2.get("region"):
            score += 0.4
        total_weight += 0.4
        
        # 도로 유형 비교 (가중치: 0.3)
        if filter1.get("road_type") == filter2.get("road_type"):
            score += 0.3
        total_weight += 0.3
        
        # 키워드 유사도 (가중치: 0.3)
        keyword1 = filter1.get("keyword", "").lower()
        keyword2 = filter2.get("keyword", "").lower()
        
        if keyword1 and keyword2:
            # 간단한 문자열 유사도 계산
            common_chars = set(keyword1) & set(keyword2)
            if common_chars:
                similarity = len(common_chars) / max(len(keyword1),
                                                  len(keyword2))
                score += 0.3 * similarity
            total_weight += 0.3
            
        return score / total_weight if total_weight > 0 else 0.0 