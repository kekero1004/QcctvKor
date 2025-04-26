from typing import Dict, List, Optional
import json
import base64
import zlib
from datetime import datetime
from ..utils.logger import Logger
from ..utils.exceptions import ConfigError

logger = Logger.get_logger()

class FilterShare:
    @staticmethod
    def export_filter(filter_config: Dict, name: str) -> str:
        """Export filter to shareable string"""
        try:
            # 필터 데이터 준비
            share_data = {
                "name": name,
                "config": filter_config,
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # JSON 직렬화
            json_data = json.dumps(share_data, ensure_ascii=False)
            
            # 압축 및 인코딩
            compressed = zlib.compress(json_data.encode('utf-8'))
            encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
            
            logger.info(f"필터 '{name}' 내보내기 완료")
            return encoded
            
        except Exception as e:
            logger.error(f"필터 내보내기 실패: {str(e)}")
            raise ConfigError(f"필터 내보내기 실패: {str(e)}")
            
    @staticmethod
    def import_filter(share_string: str) -> Dict:
        """Import filter from shareable string"""
        try:
            # 디코딩 및 압축 해제
            decoded = base64.urlsafe_b64decode(share_string.encode('ascii'))
            decompressed = zlib.decompress(decoded)
            
            # JSON 파싱
            share_data = json.loads(decompressed.decode('utf-8'))
            
            # 버전 확인
            if share_data.get("version") != "1.0":
                raise ConfigError("지원하지 않는 필터 버전입니다.")
                
            logger.info(f"필터 '{share_data['name']}' 가져오기 완료")
            return {
                "name": share_data["name"],
                "config": share_data["config"],
                "imported_at": datetime.now().isoformat(),
                "original_created_at": share_data["created_at"]
            }
            
        except Exception as e:
            logger.error(f"필터 가져오기 실패: {str(e)}")
            raise ConfigError(f"필터 가져오기 실패: {str(e)}")
            
    @staticmethod
    def validate_share_string(share_string: str) -> bool:
        """Validate filter share string"""
        try:
            decoded = base64.urlsafe_b64decode(share_string.encode('ascii'))
            decompressed = zlib.decompress(decoded)
            share_data = json.loads(decompressed.decode('utf-8'))
            
            required_fields = ["name", "config", "created_at", "version"]
            return all(field in share_data for field in required_fields)
            
        except Exception:
            return False 