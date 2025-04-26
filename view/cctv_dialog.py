from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel,
                             QHBoxLayout, QWidget, QFileDialog, QMessageBox,
                             QComboBox, QLineEdit, QProgressBar)
from qgis.PyQt.QtCore import QTimer, Qt, QUrl
# QGIS PyQt에 없는 멀티미디어 모듈은 PyQt5에서 직접 임포트
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from qgis.PyQt.QtGui import QImage, QPixmap
from datetime import datetime
import os
import cv2
import numpy as np
from typing import Dict
from .auto_filter_dialog import AutoFilterDialog
from ..model.filter_auto import FilterAuto
from .combine_filter_dialog import CombineFilterDialog
from ..model.filter_combine import FilterCombine
from .recommend_dialog import RecommendDialog
from ..model.filter_recommend import FilterRecommend
from ..model.cctv_model import CctvModel

class CctvDialog(QDialog):
    def __init__(self, cctv_info=None, parent=None, iface=None):
        super().__init__(parent)
        self.iface = iface
        # CCTV 정보가 없으면 기본값 설정
        self.cctv_info = cctv_info or {
            'name': '샘플 CCTV',
            'url': '',  # 비어있는 URL
            'lat': 0.0,
            'lon': 0.0
        }
        self.model = CctvModel()
        self.filter_auto = FilterAuto()
        self.auto_filter_timer = QTimer()
        self.auto_filter_timer.timeout.connect(self._check_auto_filters)
        self.auto_filter_timer.start(60000)  # 1분마다 체크
        self.filter_combine = FilterCombine()
        self.filter_recommend = FilterRecommend()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize UI components"""
        self.setWindowTitle(f"CCTV View - {self.cctv_info['name']}")
        self.setMinimumSize(800, 600)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Top panel for filters
        top_panel = QHBoxLayout()
        
        # Region filter
        region_label = QLabel("지역:")
        self.region_combo = QComboBox()
        self.region_combo.addItems(["전체", "서울", "경기", "인천", "부산"])
        self.region_combo.currentTextChanged.connect(self.apply_filters)
        
        # Road type filter
        road_label = QLabel("도로:")
        self.road_combo = QComboBox()
        self.road_combo.addItems(["전체", "고속도로", "국도", "시도"])
        self.road_combo.currentTextChanged.connect(self.apply_filters)
        
        # Search box
        search_label = QLabel("검색:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("CCTV 이름으로 검색...")
        self.search_input.textChanged.connect(self.search_cctv)
        
        # Add filter controls to top panel
        top_panel.addWidget(region_label)
        top_panel.addWidget(self.region_combo)
        top_panel.addWidget(road_label)
        top_panel.addWidget(self.road_combo)
        top_panel.addWidget(search_label)
        top_panel.addWidget(self.search_input)
        
        # Add top panel to main layout
        top_widget = QWidget()
        top_widget.setLayout(top_panel)
        layout.addWidget(top_widget)
        
        # Video player
        self.setup_video_player()
        layout.addWidget(self.video_player)
        
        # Bottom panel
        bottom_panel = QHBoxLayout()
        
        # Time display
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.update_current_time()
        
        # Setup timer for time updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_current_time)
        self.timer.start(1000)  # Update every second
        
        # Capture button
        capture_btn = QPushButton("캡처")
        capture_btn.clicked.connect(self.capture_frame)
        
        # Add widgets to bottom panel
        bottom_panel.addWidget(self.time_label)
        bottom_panel.addWidget(capture_btn)
        
        # Add bottom panel to main layout
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_panel)
        layout.addWidget(bottom_widget)
        
        # 필터 관리 버튼 추가
        filter_btn_layout = QHBoxLayout()
        auto_filter_btn = QPushButton("자동 필터 설정")
        auto_filter_btn.clicked.connect(self._show_auto_filter_dialog)
        combine_filter_btn = QPushButton("필터 조합")
        combine_filter_btn.clicked.connect(self._show_combine_filter_dialog)
        recommend_filter_btn = QPushButton("필터 추천")
        recommend_filter_btn.clicked.connect(self._show_recommend_dialog)
        
        filter_btn_layout.addWidget(auto_filter_btn)
        filter_btn_layout.addWidget(combine_filter_btn)
        filter_btn_layout.addWidget(recommend_filter_btn)
        layout.addLayout(filter_btn_layout)
        
        self.setLayout(layout)
        
    def setup_video_player(self) -> None:
        """Setup video streaming component"""
        try:
            # URL이 비어있는 경우 처리
            if not self.cctv_info['url']:
                self.video_player = QLabel("비디오 스트림 없음")
                self.video_player.setAlignment(Qt.AlignCenter)
                self.video_player.setStyleSheet("color: gray; font-size: 14px;")
                return
            
            # OpenCV를 사용하여 비디오 캡처 설정
            self.video_capture = cv2.VideoCapture(self.cctv_info['url'])
            if not self.video_capture.isOpened():
                raise Exception("Failed to open video stream")
            
            # 비디오 표시를 위한 QLabel 생성
            self.video_player = QLabel()
            self.video_player.setAlignment(Qt.AlignCenter)
            
            # 프레임 업데이트 타이머 설정
            self.frame_timer = QTimer()
            self.frame_timer.timeout.connect(self.update_frame)
            self.frame_timer.start(30)  # 30ms 간격으로 프레임 업데이트 (약 33fps)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup video player: {str(e)}")
            self.close()
        
    def update_frame(self) -> None:
        """Update video frame"""
        if self.video_capture and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                # OpenCV BGR을 RGB로 변환
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                
                # QImage로 변환
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # QLabel에 표시
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    self.video_player.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.video_player.setPixmap(scaled_pixmap)
        
    def update_current_time(self) -> None:
        """Update current time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def capture_frame(self) -> None:
        """Capture current frame as image"""
        if not self.video_capture or not self.video_capture.isOpened():
            QMessageBox.warning(self, "Warning", "No video stream available")
            return
            
        # Get save file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Capture", "", "Images (*.png *.jpg)"
        )
        
        if file_path:
            try:
                # 현재 프레임 캡처
                ret, frame = self.video_capture.read()
                if ret:
                    # 파일 확장자에 따라 이미지 저장
                    if file_path.lower().endswith('.jpg'):
                        cv2.imwrite(file_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    else:  # PNG
                        cv2.imwrite(file_path, frame)
                    
                    QMessageBox.information(
                        self, "Success", f"Frame captured and saved to:\n{file_path}"
                    )
                else:
                    raise Exception("Failed to capture frame")
                    
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save capture: {str(e)}"
                )
        
    def closeEvent(self, event) -> None:
        """Handle dialog close event"""
        if self.timer:
            self.timer.stop()
        if self.frame_timer:
            self.frame_timer.stop()
        if self.video_capture:
            self.video_capture.release()
        event.accept() 
        
    def on_data_loaded(self, success: bool) -> None:
        """Handle data loading completion"""
        self.progress_bar.setVisible(False)
        if not success:
            QMessageBox.warning(
                self,
                "데이터 로딩 실패",
                "CCTV 데이터를 불러오는데 실패했습니다."
            )
            
    def update_progress(self, current: int, total: int) -> None:
        """Update progress bar"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
    def apply_filters(self) -> None:
        """Apply selected filters"""
        self.progress_bar.setVisible(True)
        region = self.region_combo.currentText()
        road_type = self.road_combo.currentText()
        
        # Convert "전체" to None for the model
        region = None if region == "전체" else region
        road_type = None if road_type == "전체" else road_type
        
        # Apply filters through the model
        self.model.filter_cctv_data(region, road_type)
        self.progress_bar.setVisible(False)
        
    def search_cctv(self) -> None:
        """Search CCTV by name"""
        keyword = self.search_input.text().strip()
        results = self.model.search_cctv(keyword)
        
        # Update the view with search results
        # TODO: Implement result display
        print(f"Found {len(results)} CCTVs matching '{keyword}'") 
        
    def _show_auto_filter_dialog(self):
        """Show automatic filter configuration dialog"""
        try:
            # 현재 필터 설정 가져오기
            filter_config = {
                "name": "",
                "region": self.region_combo.currentText(),
                "road_type": self.road_combo.currentText(),
                "keyword": self.search_input.text()
            }
            
            dialog = AutoFilterDialog(filter_config, self)
            if dialog.exec_() == QDialog.Accepted:
                QMessageBox.information(self, "알림", "자동 필터가 설정되었습니다.")
                
        except Exception as e:
            logger.error(f"자동 필터 설정 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"자동 필터 설정 실패: {str(e)}")
            
    def _check_auto_filters(self):
        """Check and apply automatic filters"""
        try:
            due_filters = self.filter_auto.get_due_filters()
            for filter_data in due_filters:
                config = filter_data["config"]
                
                # 필터 적용
                self.region_combo.setCurrentText(config["region"])
                self.road_combo.setCurrentText(config["road_type"])
                self.search_input.setText(config["keyword"])
                self.apply_filter()
                
                # 실행 시간 업데이트
                self.filter_auto.update_last_run(filter_data["name"])
                logger.info(f"자동 필터 '{filter_data['name']}' 실행됨")
                
        except Exception as e:
            logger.error(f"자동 필터 실행 실패: {str(e)}")
            
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.auto_filter_timer.stop()
        super().closeEvent(event) 
        
    def _show_combine_filter_dialog(self):
        """Show filter combination dialog"""
        try:
            # 현재 필터 설정 가져오기
            current_filter = {
                "region": self.region_combo.currentText(),
                "road_type": self.road_combo.currentText(),
                "keyword": self.search_input.text()
            }
            
            dialog = CombineFilterDialog(current_filter, self)
            dialog.filter_applied.connect(self._apply_combined_filter)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"필터 조합 대화상자 표시 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"필터 조합 대화상자 표시 실패: {str(e)}")
            
    def _apply_combined_filter(self, filter_name: str):
        """Apply combined filter"""
        try:
            # 원본 데이터에 조합 필터 적용
            filtered_data = self.filter_combine.apply_combined_filter(
                filter_name, self.model.get_all_data())
                
            # 결과 표시
            self.model.set_filtered_data(filtered_data)
            self.update_results_display()
            
            logger.info(f"조합 필터 '{filter_name}' 적용됨")
            
        except Exception as e:
            logger.error(f"조합 필터 적용 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"조합 필터 적용 실패: {str(e)}") 
        
    def _show_recommend_dialog(self):
        """Show filter recommendation dialog"""
        try:
            # 현재 필터 설정 가져오기
            current_filter = {
                "region": self.region_combo.currentText(),
                "road_type": self.road_combo.currentText(),
                "keyword": self.search_input.text()
            }
            
            dialog = RecommendDialog(current_filter, self)
            dialog.filter_selected.connect(self._apply_recommended_filter)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"필터 추천 대화상자 표시 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"필터 추천 대화상자 표시 실패: {str(e)}")
            
    def _apply_recommended_filter(self, filter_config: Dict):
        """Apply recommended filter"""
        try:
            # 필터 설정 적용
            self.region_combo.setCurrentText(filter_config["region"])
            self.road_combo.setCurrentText(filter_config["road_type"])
            self.search_input.setText(filter_config["keyword"])
            
            # 필터 적용
            self.apply_filter()
            
            # 사용 기록 저장
            self.filter_recommend.save_filter_usage(filter_config)
            
            logger.info("추천 필터가 적용되었습니다.")
            
        except Exception as e:
            logger.error(f"추천 필터 적용 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"추천 필터 적용 실패: {str(e)}")
            
    def apply_filter(self):
        """Apply current filter settings"""
        try:
            # 현재 필터 설정 가져오기
            filter_config = {
                "region": self.region_combo.currentText(),
                "road_type": self.road_combo.currentText(),
                "keyword": self.search_input.text()
            }
            
            # 필터 적용
            filtered_data = self.model.apply_filter(filter_config)
            self.update_results_display()
            
            # 사용 기록 저장
            self.filter_recommend.save_filter_usage(filter_config)
            
            logger.info("필터가 적용되었습니다.")
            
        except Exception as e:
            logger.error(f"필터 적용 실패: {str(e)}")
            QMessageBox.critical(self, "오류", f"필터 적용 실패: {str(e)}") 