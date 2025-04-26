from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel,
                             QLineEdit, QMessageBox)
from qgis.PyQt.QtCore import QSettings
import os
from ..utils.config_manager import ConfigManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 구성 관리자 인스턴스 생성
        self.config_manager = ConfigManager()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize UI components"""
        self.setWindowTitle("QcctvKor 설정")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # API Key input
        api_key_label = QLabel("ITS API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        
        # config.ini에서 API 키 가져오기
        self.api_key_input.setText(self.config_manager.get_api_key())
        
        # Help text
        help_text = QLabel(
            "ITS API 키는 <a href='http://openapi.its.go.kr'>http://openapi.its.go.kr</a>에서 발급받을 수 있습니다."
        )
        help_text.setOpenExternalLinks(True)
        help_text.setWordWrap(True)
        
        # Save button
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_settings)
        
        # Add widgets to layout
        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(help_text)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
        
    def save_settings(self) -> None:
        """Save settings to config.ini"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(
                self,
                "경고",
                "API 키를 입력해주세요."
            )
            return
            
        # config.ini 파일에 API 키 저장
        self.config_manager.set_api_key(api_key)
        
        QMessageBox.information(
            self,
            "성공",
            "설정이 저장되었습니다."
        )
        self.accept() 