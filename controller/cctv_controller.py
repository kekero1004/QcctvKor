from qgis.gui import QgisInterface, QgsMapToolIdentifyFeature
from qgis.core import QgsProject, Qgis
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog, QToolButton, QMenu
from qgis.PyQt.QtGui import QIcon
from ..model.cctv_model import CctvModel
from ..view.cctv_dialog import CctvDialog
from ..view.settings_dialog import SettingsDialog
from ..view.api_key_dialog import ApiKeyDialog
from ..utils.config_manager import ConfigManager
import os

class CctvController:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.model = CctvModel()
        self.dialog = None
        self.action = None
        self.api_key_action = None
        self.map_tool = None
        
    def initGui(self) -> None:
        """Initialize plugin components - QGIS Plugin required method"""
        # Create plugin menu item
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        self.action = QAction(
            QIcon(icon_path),
            "QcctvKor",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.show_cctv_layer)
        
        # API 키 설정 메뉴 아이템
        self.api_key_action = QAction(
            QIcon(icon_path),
            "ITS API 키 설정",
            self.iface.mainWindow()
        )
        self.api_key_action.triggered.connect(self.show_api_key_dialog)
        
        # 메뉴에 아이템 추가
        self.iface.addPluginToMenu("QcctvKor", self.action)
        self.iface.addPluginToMenu("QcctvKor", self.api_key_action)
        self.iface.addToolBarIcon(self.action)
        
    def show_api_key_dialog(self) -> None:
        """API 키 설정 대화상자 표시"""
        dialog = ApiKeyDialog(self.iface.mainWindow())
        dialog.exec_()
        
    def show_cctv_layer(self) -> None:
        """Show CCTV points on map"""
        # API 키 확인
        config_manager = ConfigManager()
        has_api_key = bool(config_manager.get_api_key())
        
        # 기본 CCTV 정보 (API 키가 없는 경우 사용)
        default_cctv_info = {
            'name': 'CCTV 뷰어',
            'url': '',  # 비어있는 URL
            'lat': 37.5665,  # 서울 중심 좌표
            'lon': 126.9780
        }
        
        try:
            if not has_api_key:
                # API 키가 없는 경우 경고 메시지 표시 후 기본 대화상자 열기
                QMessageBox.warning(
                    self.iface.mainWindow(),
                    "API 키 필요",
                    "ITS API 키가 입력되지 않아 CCTV 레이어를 불러오는 데 실패했습니다.\n'플러그인 > QcctvKor > ITS API 키 설정' 메뉴에서 API 키를 설정해주세요."
                )
                
                # 기본 CCTV 대화상자 표시
                self.show_cctv_dialog(default_cctv_info)
                return
            
            # API 키가 있는 경우 정상적으로 CCTV 데이터 로드
            self.model.load_cctv_data()
            
            # Create temporary layer
            self.model.create_temp_layer()
            
            # Add CCTV points to layer
            for cctv in self.model.cctv_data:
                self.model.add_cctv_feature(
                    cctv["name"],
                    cctv["url"],
                    cctv["lat"],
                    cctv["lon"]
                )
            
            # Set up map tool for feature identification
            self.map_tool = QgsMapToolIdentifyFeature(self.iface.mapCanvas())
            self.map_tool.featureIdentified.connect(self.handle_feature_click)
            self.iface.mapCanvas().setMapTool(self.map_tool)
            
        except Exception as e:
            # 오류 발생 시 오류 메시지 표시 후 기본 대화상자 열기
            QMessageBox.critical(
                self.iface.mainWindow(),
                "오류",
                f"CCTV 레이어를 불러오는 데 실패했습니다: {str(e)}"
            )
            
            # 기본 CCTV 대화상자 표시
            self.show_cctv_dialog(default_cctv_info)
        
    def handle_feature_click(self, feature) -> None:
        """Handle CCTV point click event"""
        try:
            # Get CCTV info for clicked feature
            cctv_info = self.model.get_cctv_info(feature.id())
            
            # Show CCTV dialog
            self.show_cctv_dialog(cctv_info)
            
        except Exception as e:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Warning",
                f"Failed to show CCTV stream: {str(e)}"
            )
        
    def show_cctv_dialog(self, cctv_info: dict) -> None:
        """Show CCTV streaming dialog"""
        if self.dialog:
            self.dialog.close()
            
        self.dialog = CctvDialog(cctv_info, self.iface.mainWindow(), self.iface)
        self.dialog.finished.connect(self.cleanup)
        self.dialog.show()
        
    def cleanup(self) -> None:
        """Clean up resources"""
        # Remove temporary layer
        self.model.remove_temp_layer()
        
        # Reset map tool
        self.iface.mapCanvas().unsetMapTool(self.map_tool)
        
        # Clear dialog reference
        self.dialog = None
        
    def unload(self) -> None:
        """Unload plugin"""
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("QcctvKor", self.action)
        self.iface.removePluginMenu("QcctvKor", self.api_key_action)
        self.iface.removeToolBarIcon(self.action)
        
        # Clean up resources
        self.cleanup() 