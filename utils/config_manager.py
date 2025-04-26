import os
import configparser
from pathlib import Path

class ConfigManager:
    """Configuration file manager for QcctvKor"""
    
    def __init__(self):
        """Initialize configuration manager"""
        # 플러그인 디렉토리 경로
        self.plugin_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 구성 파일 경로
        self.config_file = self.plugin_dir / 'config.ini'
        
        # 구성 파일이 없으면 기본 구성 파일 생성
        self._create_default_config()
        
        # 구성 파일 로드
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
    
    def _create_default_config(self):
        """기본 구성 파일 생성"""
        if not self.config_file.exists():
            config = configparser.ConfigParser()
            config['API'] = {
                'ITS_API_KEY': ''
            }
            
            with open(self.config_file, 'w') as f:
                config.write(f)
    
    def get_api_key(self):
        """ITS API 키 가져오기"""
        return self.config.get('API', 'ITS_API_KEY', fallback='')
    
    def set_api_key(self, api_key):
        """ITS API 키 설정"""
        if 'API' not in self.config:
            self.config['API'] = {}
        
        self.config['API']['ITS_API_KEY'] = api_key
        
        with open(self.config_file, 'w') as f:
            self.config.write(f)
            
        # 환경 변수에도 설정 (기존 호환성 유지)
        os.environ['ITS_API_KEY'] = api_key
        
        return True 