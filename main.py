import sys
from PySide6.QtWidgets import QApplication

from name_tag_combiner.assets import load_app_icon
from name_tag_combiner.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app_icon = load_app_icon()
    if app_icon is not None:
        app.setWindowIcon(app_icon)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
