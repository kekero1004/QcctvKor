class QcctvKorError(Exception):
    """Base exception class for QcctvKor"""
    pass

class ApiError(QcctvKorError):
    """API related errors"""
    pass

class NetworkError(QcctvKorError):
    """Network related errors"""
    pass

class DataError(QcctvKorError):
    """Data processing related errors"""
    pass

class LayerError(QcctvKorError):
    """Layer handling related errors"""
    pass

class ConfigError(QcctvKorError):
    """Configuration related errors"""
    pass

class VideoError(QcctvKorError):
    """Video streaming related errors"""
    pass

def handle_exception(error: Exception) -> QcctvKorError:
    """Convert general exceptions to QcctvKor specific exceptions"""
    if isinstance(error, QcctvKorError):
        return error
        
    error_type = type(error).__name__
    error_msg = str(error)
    
    if error_type in ['ConnectionError', 'Timeout', 'RequestException']:
        return NetworkError(f"네트워크 오류: {error_msg}")
    elif error_type in ['JSONDecodeError', 'KeyError', 'ValueError']:
        return DataError(f"데이터 처리 오류: {error_msg}")
    elif error_type in ['QgsError', 'AttributeError']:
        return LayerError(f"레이어 처리 오류: {error_msg}")
    elif error_type in ['FileNotFoundError', 'PermissionError']:
        return ConfigError(f"설정 오류: {error_msg}")
    elif error_type in ['cv2.error', 'VideoCapture']:
        return VideoError(f"비디오 스트리밍 오류: {error_msg}")
    else:
        return QcctvKorError(f"알 수 없는 오류: {error_msg}") 