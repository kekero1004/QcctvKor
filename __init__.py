def classFactory(iface):
    from .controller.cctv_controller import CctvController
    return CctvController(iface) 