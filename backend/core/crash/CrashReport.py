from core.library.Utils import Singleton


class CrashReport(Singleton):
    """
    崩溃报告
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

