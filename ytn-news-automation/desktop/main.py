import os
import sys
from dotenv import load_dotenv

from PyQt5.QtWidgets import QApplication

try:
    from desktop.ui.main_window import MainWindow
except Exception as exc:
    print(f"Failed to import UI: {exc}")
    raise


def main() -> int:
    # Load environment from multiple locations
    # 1) Bundled config when running as PyInstaller onefile
    base_dir = getattr(sys, "_MEIPASS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    load_dotenv(dotenv_path=os.path.join(base_dir, "config", ".env"), override=False)

    # 2) EXE directory .env (supports placing .env next to moved exe)
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
    load_dotenv(dotenv_path=os.path.join(exe_dir, ".env"), override=False)

    # 3) Fallback to current working directory search
    load_dotenv(override=False)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())


