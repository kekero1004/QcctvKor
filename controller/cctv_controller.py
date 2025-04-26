from qgis.gui import QgisInterface, QgsMapToolIdentifyFeature
from qgis.core import QgsProject, Qgis
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog
from qgis.PyQt.QtGui import QIcon
from ..model.cctv_model import CctvModel
from ..view.cctv_dialog import CctvDialog
from ..view.settings_dialog import SettingsDialog
import os
from ..utils.config_manager import ConfigManager

class CctvController:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.model = CctvModel()
        self.dialog = None
        self.action = None
        self.map_tool = None
        
    def initialize_plugin(self) -> None:
        """Initialize plugin components"""
        # Create plugin menu item
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        self.action = QAction(
            QIcon(icon_path),
            "QcctvKor",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.show_cctv_layer)
        
        # Add menu items to QGIS
        self.iface.addPluginToMenu("QcctvKor", self.action)
        self.iface.addToolBarIcon(self.action)
        
    def show_cctv_layer(self) -> None:
        """Show CCTV points on map"""
        try:
            # API 키 확인 및 설정 대화상자 표시
            config_manager = ConfigManager()
            
            if not config_manager.get_api_key():
                QMessageBox.information(
                    self.iface.mainWindow(),
                    "API 키 필요",
                    "CCTV 데이터를 불러오기 위해 ITS API 키를 입력해 주세요."
                )
                dialog = SettingsDialog(self.iface.mainWindow())
                result = dialog.exec_()
                
                # 사용자가 취소한 경우 종료
                if result != QDialog.Accepted:
                    return
                
                # API 키가 여전히 설정되지 않은 경우 종료
                if not config_manager.get_api_key():
                    return
            
            # Load CCTV data
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
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Error",
                f"Failed to load CCTV layer: {str(e)}"
            )
        
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
            
        self.dialog = CctvDialog(cctv_info, self.iface.mainWindow())
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
        self.iface.removeToolBarIcon(self.action)
        
        # Clean up resources
        self.cleanup() 