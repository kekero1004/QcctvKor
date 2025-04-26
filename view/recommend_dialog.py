from typing import Dict, List
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QListWidget, QListWidgetItem, QProgressBar)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from ..model.filter_recommend import FilterRecommend
from ..utils.logger import Logger

logger = Logger.get_logger()

class RecommendDialog(QDialog):
    filter_selected = pyqtSignal(dict)  # 필터 선택 시그널
    
    def __init__(self, current_filter: Dict, parent=None):
        super().__init__(parent)
        self.current_filter = current_filter
        self.filter_recommend = FilterRecommend()
        self.setup_ui()
        self.load_recommendations()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("필터 추천")
        self.setMinimumWidth(400)
        
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
        
        # 추천 필터 목록
        recommendations_label = QLabel("추천 필터:")
        self.recommendations_list = QListWidget()
        self.recommendations_list.itemDoubleClicked.connect(
            self._on_filter_selected)
        layout.addWidget(recommendations_label)
        layout.addWidget(self.recommendations_list)
        
        # 버튼
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("적용")
        apply_btn.clicked.connect(self._apply_selected_filter)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_recommendations(self):
        """Load and display filter recommendations"""
        try:
            recommendations = self.filter_recommend.get_recommendations(
                self.current_filter)
                
            self.recommendations_list.clear()
            
            for rec in recommendations:
                filter_config = rec["filter"]
                reason = rec["reason"]
                confidence = rec["confidence"]
                
                # 필터 정보 텍스트 생성
                filter_text = (
                    f"지역: {filter_config.get('region', '전체')}, "
                    f"도로 유형: {filter_config.get('road_type', '전체')}, "
                    f"키워드: {filter_config.get('keyword', '')}"
                )
                
                # 아이템 생성
                item = QListWidgetItem()
                item.setData(Qt.UserRole, filter_config)
                
                # 아이템 위젯 생성
                widget = QWidget()
                layout = QVBoxLayout()
                
                # 필터 정보
                filter_label = QLabel(filter_text)
                filter_label.setWordWrap(True)
                layout.addWidget(filter_label)
                
                # 추천 이유
                reason_label = QLabel(reason)
                reason_label.setStyleSheet("color: gray;")
                layout.addWidget(reason_label)
                
                # 신뢰도 바
                confidence_layout = QHBoxLayout()
                confidence_label = QLabel("추천 신뢰도:")
                confidence_bar = QProgressBar()
                confidence_bar.setMaximum(100)
                confidence_bar.setValue(int(confidence * 100))
                confidence_bar.setTextVisible(False)
                confidence_bar.setFixedHeight(10)
                
                confidence_layout.addWidget(confidence_label)
                confidence_layout.addWidget(confidence_bar)
                layout.addLayout(confidence_layout)
                
                widget.setLayout(layout)
                
                # 아이템 크기 설정
                item.setSizeHint(widget.sizeHint())
                
                # 아이템 추가
                self.recommendations_list.addItem(item)
                self.recommendations_list.setItemWidget(item, widget)
                
        except Exception as e:
            logger.error(f"필터 추천 로드 실패: {str(e)}")
            
    def _on_filter_selected(self, item: QListWidgetItem):
        """Handle filter selection"""
        filter_config = item.data(Qt.UserRole)
        self.filter_selected.emit(filter_config)
        self.accept()
        
    def _apply_selected_filter(self):
        """Apply selected filter"""
        current = self.recommendations_list.currentItem()
        if current:
            self._on_filter_selected(current) 