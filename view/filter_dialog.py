from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QLineEdit, QMessageBox,
                             QDialogButtonBox, QInputDialog)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from ..model.filter_settings import FilterSettings
from ..utils.logger import Logger

logger = Logger.get_logger()

class FilterDialog(QDialog):
    filter_selected = pyqtSignal(dict)  # 필터 선택 시그널
    
    def __init__(self, current_filter: dict = None, parent=None):
        super().__init__(parent)
        self.filter_settings = FilterSettings()
        self.current_filter = current_filter
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize UI components"""
        self.setWindowTitle("필터 관리")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # 필터 목록
        list_layout = QHBoxLayout()
        
        # 왼쪽 패널: 필터 목록
        self.filter_list = QListWidget()
        self.filter_list.itemSelectionChanged.connect(self.on_selection_changed)
        list_layout.addWidget(self.filter_list)
        
        # 오른쪽 패널: 버튼들
        button_layout = QVBoxLayout()
        
        save_btn = QPushButton("현재 필터 저장")
        save_btn.clicked.connect(self.save_current_filter)
        
        load_btn = QPushButton("필터 불러오기")
        load_btn.clicked.connect(self.load_selected_filter)
        load_btn.setEnabled(False)
        self.load_btn = load_btn
        
        delete_btn = QPushButton("필터 삭제")
        delete_btn.clicked.connect(self.delete_selected_filter)
        delete_btn.setEnabled(False)
        self.delete_btn = delete_btn
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        list_layout.addLayout(button_layout)
        layout.addLayout(list_layout)
        
        # 필터 정보 표시
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # 닫기 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # 필터 목록 로드
        self.load_filter_list()
        
    def load_filter_list(self) -> None:
        """Load saved filters into list widget"""
        self.filter_list.clear()
        filters = self.filter_settings.get_saved_filters()
        for name in filters.keys():
            self.filter_list.addItem(name)
            
    def on_selection_changed(self) -> None:
        """Handle filter selection change"""
        selected_items = self.filter_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.load_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            name = selected_items[0].text()
            filter_info = self.filter_settings.get_filter_info(name)
            if filter_info:
                created = filter_info["created_at"].split("T")[0]
                last_used = filter_info["last_used"].split("T")[0]
                self.info_label.setText(
                    f"생성일: {created}\n"
                    f"마지막 사용: {last_used}"
                )
        else:
            self.info_label.clear()
            
    def save_current_filter(self) -> None:
        """Save current filter configuration"""
        if not self.current_filter:
            QMessageBox.warning(
                self,
                "경고",
                "저장할 필터가 없습니다."
            )
            return
            
        name, ok = QInputDialog.getText(
            self,
            "필터 저장",
            "필터 이름을 입력하세요:"
        )
        
        if ok and name:
            try:
                self.filter_settings.save_filter(name, self.current_filter)
                self.load_filter_list()
                QMessageBox.information(
                    self,
                    "성공",
                    f"필터 '{name}'이(가) 저장되었습니다."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "오류",
                    f"필터 저장 실패: {str(e)}"
                )
                
    def load_selected_filter(self) -> None:
        """Load selected filter"""
        selected_items = self.filter_list.selectedItems()
        if not selected_items:
            return
            
        name = selected_items[0].text()
        try:
            filter_config = self.filter_settings.load_filter(name)
            if filter_config:
                self.filter_selected.emit(filter_config)
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "경고",
                    f"필터 '{name}'을(를) 찾을 수 없습니다."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"필터 로드 실패: {str(e)}"
            )
            
    def delete_selected_filter(self) -> None:
        """Delete selected filter"""
        selected_items = self.filter_list.selectedItems()
        if not selected_items:
            return
            
        name = selected_items[0].text()
        reply = QMessageBox.question(
            self,
            "확인",
            f"필터 '{name}'을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.filter_settings.delete_filter(name):
                    self.load_filter_list()
                    QMessageBox.information(
                        self,
                        "성공",
                        f"필터 '{name}'이(가) 삭제되었습니다."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "경고",
                        f"필터 '{name}'을(를) 찾을 수 없습니다."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "오류",
                    f"필터 삭제 실패: {str(e)}"
                ) 