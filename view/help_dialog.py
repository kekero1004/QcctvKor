from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextBrowser
from qgis.PyQt.QtCore import Qt, QUrl
import os

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize UI components"""
        self.setWindowTitle("QcctvKor 도움말")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Manual browser
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        
        # Load manual content
        manual_path = os.path.join(os.path.dirname(__file__), "..", "resources", "manual.html")
        if os.path.exists(manual_path):
            with open(manual_path, 'r', encoding='utf-8') as f:
                self.browser.setHtml(f.read())
        else:
            self.browser.setPlainText("매뉴얼 파일을 찾을 수 없습니다.")
        
        # Close button
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        
        # Add widgets to layout
        layout.addWidget(self.browser)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
    def show_section(self, section: str) -> None:
        """Show specific section of the manual"""
        # Find and scroll to the section
        cursor = self.browser.document().find(section)
        if not cursor.isNull():
            self.browser.setTextCursor(cursor)
            self.browser.ensureCursorVisible() 