from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel,
                             QLineEdit, QMessageBox)
from qgis.PyQt.QtCore import Qt
from ..utils.config_manager import ConfigManager

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """API 키 입력 대화상자 UI 구성"""
        self.setWindowTitle("ITS API 키 입력")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f8f8;
            }
            QLabel {
                font-size: 12px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 헤더 레이블
        header_label = QLabel("ITS API 키 설정")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        
        # API Key 입력 필드
        api_key_label = QLabel("ITS API 키를 입력해주세요:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API 키 입력...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        
        # 현재 저장된 API 키 가져오기
        current_key = self.config_manager.get_api_key()
        if current_key:
            self.api_key_input.setText(current_key)
        
        # 도움말 텍스트
        help_text = QLabel(
            "ITS API 키는 <a href='http://openapi.its.go.kr'>http://openapi.its.go.kr</a>에서 발급받을 수 있습니다."
        )
        help_text.setOpenExternalLinks(True)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        
        # 버튼 레이아웃
        button_layout = QVBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_api_key)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet("background-color: #f44336;")
        cancel_btn.clicked.connect(self.reject)
        
        # 위젯을 레이아웃에 추가
        layout.addWidget(header_label)
        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(help_text)
        layout.addSpacing(10)
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)
        
    def save_api_key(self) -> None:
        """API 키 저장"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(
                self,
                "경고",
                "API 키를 입력해주세요."
            )
            return
            
        # API 키를 config.ini 파일에 저장
        self.config_manager.set_api_key(api_key)
        
        QMessageBox.information(
            self,
            "성공",
            "API 키가 저장되었습니다."
        )
        self.accept() 