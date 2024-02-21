from core.library.Utils import ThreadSafeSingleton
import datetime


class Colors:
    HEADER = '\033[95m'
    END = '\033[0m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    MAIN = '\033[0;30;43m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger(ThreadSafeSingleton):
    __logs = []  # 系统日志

    def __init__(self):
        super().__init__()

    @classmethod
    def info(cls, *msg):
        t = datetime.datetime.now()
        s = ' '.join([str(s) for s in msg])
        cls.update_message_pool(f"[   Info   ] {t.strftime('%H:%M:%S')} {s}")
        print(
            f"{Colors.CYAN} [   Info   ] {t.strftime('%H:%M:%S')}{Colors.END} {s}")

    @classmethod
    def output(cls, *msg):
        t = datetime.datetime.now()
        s = ' '.join([str(s) for s in msg])
        cls.update_message_pool(f"[  Output  ] {t.strftime('%H:%M:%S')} {s}")
        print(
            f"{Colors.BLUE} [  Output  ] {t.strftime('%H:%M:%S')}{Colors.END} {s}")

    @classmethod
    def warn(cls, *msg):
        t = datetime.datetime.now()
        s = ' '.join([str(s) for s in msg])
        cls.update_message_pool(f"[   Warn   ] {t.strftime('%H:%M:%S')} {s}")
        print(
            f"{Colors.WARNING} [   Warn   ] {t.strftime('%H:%M:%S')}{Colors.END} {s}")

    @classmethod
    def danger(cls, *msg):
        t = datetime.datetime.now()
        s = ' '.join([str(s) for s in msg])
        cls.update_message_pool(f"[  Failed  ] {t.strftime('%H:%M:%S')} {s}")
        print(
            f"{Colors.FAIL} [  Failed  ] {t.strftime('%H:%M:%S')}{Colors.END} {s}")

    @classmethod
    def main(cls, *msg):
        t = datetime.datetime.now()
        s = ' '.join([str(s) for s in msg])
        cls.update_message_pool(f"[MainThread] {t.strftime('%H:%M:%S')} {s}")
        print(
            f"{Colors.MAIN} [MainThread] {t.strftime('%H:%M:%S')} {s}{Colors.END}")

    @classmethod
    def output_logs(cls):
        return cls.__logs

    @classmethod
    def update_message_pool(cls, string):
        cls.__logs.append(string)
