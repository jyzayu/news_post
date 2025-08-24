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
    # Load environment
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env"), override=False)
    # Fallback to project root .env
    load_dotenv(override=False)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())


