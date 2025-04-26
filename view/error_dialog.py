from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel,
                             QTextEdit, QDialogButtonBox)
from qgis.PyQt.QtCore import Qt
from ..utils.exceptions import QcctvKorError
from ..utils.logger import Logger

logger = Logger.get_logger()

class ErrorDialog(QDialog):
    def __init__(self, error: Exception, parent=None):
        super().__init__(parent)
        self.error = error
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize UI components"""
        self.setWindowTitle("오류 발생")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Error icon and message
        message = QLabel()
        if isinstance(self.error, QcctvKorError):
            message.setText(str(self.error))
        else:
            message.setText("알 수 없는 오류가 발생했습니다.")
        message.setWordWrap(True)
        message.setStyleSheet("color: red; font-weight: bold;")
        
        # Detailed error information
        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(self._get_error_details())
        details.setFixedHeight(100)
        
        # Buttons
        button_box = QDialogButtonBox()
        copy_btn = button_box.addButton("복사", QDialogButtonBox.ActionRole)
        close_btn = button_box.addButton("닫기", QDialogButtonBox.RejectRole)
        
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(details.toPlainText()))
        close_btn.clicked.connect(self.reject)
        
        # Add widgets to layout
        layout.addWidget(message)
        layout.addWidget(QLabel("상세 정보:"))
        layout.addWidget(details)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _get_error_details(self) -> str:
        """Get detailed error information"""
        details = []
        details.append(f"오류 유형: {type(self.error).__name__}")
        details.append(f"오류 메시지: {str(self.error)}")
        
        if hasattr(self.error, '__cause__') and self.error.__cause__:
            details.append(f"\n원인: {str(self.error.__cause__)}")
            
        return "\n".join(details)
        
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy error details to clipboard"""
        try:
            from qgis.PyQt.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            logger.info("오류 정보가 클립보드에 복사되었습니다.")
        except Exception as e:
            logger.error(f"클립보드 복사 실패: {str(e)}")
            
    @staticmethod
    def show_error(error: Exception, parent=None) -> None:
        """Show error dialog"""
        logger.error(f"오류 발생: {str(error)}")
        dialog = ErrorDialog(error, parent)
        dialog.exec_() 