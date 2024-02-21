from core.library.Utils import Singleton


class CrashMonitor(Singleton):
    """
    异常监控
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
