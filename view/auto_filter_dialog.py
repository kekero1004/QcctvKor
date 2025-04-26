from typing import Dict, Optional
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QLineEdit, QSpinBox, QComboBox, QTimeEdit,
                           QListWidget, QMessageBox, QCheckBox)
from qgis.PyQt.QtCore import Qt, QTime
from ..model.filter_auto import FilterAuto
from ..utils.logger import Logger

logger = Logger.get_logger()

class AutoFilterDialog(QDialog):
    def __init__(self, filter_config: Dict, parent=None):
        super().__init__(parent)
        self.filter_config = filter_config
        self.filter_auto = FilterAuto()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("자동 필터 설정")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # 필터 이름
        name_layout = QHBoxLayout()
        name_label = QLabel("필터 이름:")
        self.name_input = QLineEdit()
        self.name_input.setText(self.filter_config.get("name", ""))
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 실행 방식 선택
        schedule_type_layout = QHBoxLayout()
        schedule_label = QLabel("실행 방식:")
        self.schedule_type = QComboBox()
        self.schedule_type.addItems(["간격", "시간"])
        self.schedule_type.currentTextChanged.connect(self._on_schedule_type_changed)
        schedule_type_layout.addWidget(schedule_label)
        schedule_type_layout.addWidget(self.schedule_type)
        layout.addLayout(schedule_type_layout)
        
        # 간격 설정
        self.interval_layout = QHBoxLayout()
        interval_label = QLabel("실행 간격(분):")
        self.interval_input = QSpinBox()
        self.interval_input.setMinimum(1)
        self.interval_input.setMaximum(1440)  # 24시간
        self.interval_input.setValue(60)  # 기본값 1시간
        self.interval_layout.addWidget(interval_label)
        self.interval_layout.addWidget(self.interval_input)
        layout.addLayout(self.interval_layout)
        
        # 시간 설정
        self.time_layout = QVBoxLayout()
        
        # 요일 선택
        days_label = QLabel("실행 요일:")
        self.day_checks = []
        days = ["월", "화", "수", "목", "금", "토", "일"]
        days_layout = QHBoxLayout()
        
        for i, day in enumerate(days):
            check = QCheckBox(day)
            self.day_checks.append(check)
            days_layout.addWidget(check)
            
        self.time_layout.addWidget(days_label)
        self.time_layout.addLayout(days_layout)
        
        # 시간 선택
        times_label = QLabel("실행 시간:")
        self.times_list = QListWidget()
        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm")
        
        time_input_layout = QHBoxLayout()
        add_time_btn = QPushButton("추가")
        add_time_btn.clicked.connect(self._add_time)
        remove_time_btn = QPushButton("제거")
        remove_time_btn.clicked.connect(self._remove_time)
        
        time_input_layout.addWidget(self.time_input)
        time_input_layout.addWidget(add_time_btn)
        time_input_layout.addWidget(remove_time_btn)
        
        self.time_layout.addWidget(times_label)
        self.time_layout.addLayout(time_input_layout)
        self.time_layout.addWidget(self.times_list)
        
        layout.addLayout(self.time_layout)
        self.time_layout.setVisible(False)
        
        # 버튼
        button_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_auto_filter)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _on_schedule_type_changed(self, text: str):
        """Handle schedule type change"""
        is_interval = text == "간격"
        self.interval_layout.setVisible(is_interval)
        self.time_layout.setVisible(not is_interval)
        
    def _add_time(self):
        """Add time to the list"""
        time = self.time_input.time()
        time_str = time.toString("HH:mm")
        
        # 중복 확인
        items = [self.times_list.item(i).text() 
                for i in range(self.times_list.count())]
        if time_str not in items:
            self.times_list.addItem(time_str)
            
    def _remove_time(self):
        """Remove selected time from the list"""
        current = self.times_list.currentRow()
        if current >= 0:
            self.times_list.takeItem(current)
            
    def save_auto_filter(self):
        """Save automatic filter configuration"""
        try:
            name = self.name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "경고", "필터 이름을 입력하세요.")
                return
                
            self.filter_config["name"] = name
            
            # 스케줄 설정
            schedule = {}
            if self.schedule_type.currentText() == "간격":
                schedule["interval"] = self.interval_input.value()
            else:
                # 선택된 요일
                days = [i for i, check in enumerate(self.day_checks) 
                       if check.isChecked()]
                if not days:
                    QMessageBox.warning(self, "경고", "실행 요일을 선택하세요.")
                    return
                    
                # 선택된 시간
                times = [self.times_list.item(i).text() 
                        for i in range(self.times_list.count())]
                if not times:
                    QMessageBox.warning(self, "경고", "실행 시간을 추가하세요.")
                    return
                    
                schedule["days"] = days
                schedule["times"] = times
                
            self.filter_auto.save_auto_filter(self.filter_config, schedule)
            self.accept()
            
        except Exception as e:
            logger.error(f"자동 필터 저장 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"자동 필터 저장 실패: {str(e)}") 