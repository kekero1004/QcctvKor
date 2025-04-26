from typing import Dict, List, Optional
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QLineEdit, QComboBox, QListWidget,
                           QMessageBox, QRadioButton, QButtonGroup)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from ..model.filter_combine import FilterCombine
from ..utils.logger import Logger

logger = Logger.get_logger()

class CombineFilterDialog(QDialog):
    filter_applied = pyqtSignal(str)  # 필터 적용 시그널
    
    def __init__(self, current_filter: Dict, parent=None):
        super().__init__(parent)
        self.current_filter = current_filter
        self.filter_combine = FilterCombine()
        self.filters_to_combine = []
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("필터 조합")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # 현재 필터 정보
        current_filter_layout = QVBoxLayout()
        current_filter_label = QLabel("현재 필터:")
        current_filter_text = (
            f"지역: {self.current_filter.get('region', '전체')}, "
            f"도로 유형: {self.current_filter.get('road_type', '전체')}, "
            f"키워드: {self.current_filter.get('keyword', '')}"
        )
        current_filter_info = QLabel(current_filter_text)
        current_filter_layout.addWidget(current_filter_label)
        current_filter_layout.addWidget(current_filter_info)
        layout.addLayout(current_filter_layout)
        
        # 조합 이름
        name_layout = QHBoxLayout()
        name_label = QLabel("조합 이름:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 조합 연산자
        operator_layout = QHBoxLayout()
        operator_label = QLabel("조합 방식:")
        self.operator_group = QButtonGroup()
        and_radio = QRadioButton("AND (모두 만족)")
        or_radio = QRadioButton("OR (하나라도 만족)")
        and_radio.setChecked(True)
        self.operator_group.addButton(and_radio, 0)
        self.operator_group.addButton(or_radio, 1)
        operator_layout.addWidget(operator_label)
        operator_layout.addWidget(and_radio)
        operator_layout.addWidget(or_radio)
        layout.addLayout(operator_layout)
        
        # 필터 목록
        filters_label = QLabel("저장된 필터:")
        self.filters_list = QListWidget()
        self.load_saved_filters()
        layout.addWidget(filters_label)
        layout.addWidget(self.filters_list)
        
        # 필터 관리 버튼
        filter_btn_layout = QHBoxLayout()
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self._add_filter)
        remove_btn = QPushButton("제거")
        remove_btn.clicked.connect(self._remove_filter)
        filter_btn_layout.addWidget(add_btn)
        filter_btn_layout.addWidget(remove_btn)
        layout.addLayout(filter_btn_layout)
        
        # 선택된 필터 목록
        selected_label = QLabel("선택된 필터:")
        self.selected_filters_list = QListWidget()
        layout.addWidget(selected_label)
        layout.addWidget(self.selected_filters_list)
        
        # 버튼
        button_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_combined_filter)
        apply_btn = QPushButton("적용")
        apply_btn.clicked.connect(self.apply_combined_filter)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_saved_filters(self):
        """Load saved filters to the list"""
        try:
            combined_filters = self.filter_combine.get_all_combined_filters()
            
            for name, filter_data in combined_filters.items():
                self.filters_list.addItem(name)
                
        except Exception as e:
            logger.error(f"저장된 필터 로드 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"저장된 필터 로드 실패: {str(e)}")
            
    def _add_filter(self):
        """Add selected filter to combination"""
        current = self.filters_list.currentItem()
        if not current:
            return
            
        name = current.text()
        filter_data = self.filter_combine.get_combined_filter(name)
        
        if filter_data:
            self.filters_to_combine.append(filter_data)
            self.selected_filters_list.addItem(name)
            
    def _remove_filter(self):
        """Remove filter from combination"""
        current = self.selected_filters_list.currentRow()
        if current >= 0:
            self.filters_to_combine.pop(current)
            self.selected_filters_list.takeItem(current)
            
    def save_combined_filter(self):
        """Save combined filter configuration"""
        try:
            name = self.name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "경고", "조합 이름을 입력하세요.")
                return
                
            if not self.filters_to_combine:
                QMessageBox.warning(self, "경고", "필터를 선택하세요.")
                return
                
            operator = "AND" if self.operator_group.checkedId() == 0 else "OR"
            
            # 현재 필터도 포함
            filters = [self.current_filter] + [f["filters"][0] 
                                             for f in self.filters_to_combine]
            
            self.filter_combine.save_combined_filter(name, filters, operator)
            QMessageBox.information(self, "알림", "필터 조합이 저장되었습니다.")
            self.accept()
            
        except Exception as e:
            logger.error(f"필터 조합 저장 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"필터 조합 저장 실패: {str(e)}")
            
    def apply_combined_filter(self):
        """Apply selected combined filter"""
        try:
            current = self.filters_list.currentItem()
            if not current:
                QMessageBox.warning(self, "경고", "적용할 필터를 선택하세요.")
                return
                
            name = current.text()
            self.filter_applied.emit(name)
            self.accept()
            
        except Exception as e:
            logger.error(f"필터 조합 적용 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"필터 조합 적용 실패: {str(e)}") 