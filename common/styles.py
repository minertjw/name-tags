def get_shared_stylesheet() -> str:
	return """
		QMainWindow {
			background: qlineargradient(
				x1: 0, y1: 0, x2: 1, y2: 1,
				stop: 0 #f6efe4,
				stop: 0.45 #f0dfc4,
				stop: 1 #d7e4d2
			);
		}
		QWidget {
			color: #1f2a22;
			font-family: "Bahnschrift", "Trebuchet MS", sans-serif;
			font-size: 11pt;
		}
		QFrame#HeaderCard,
		QFrame#SectionCard,
		QFrame#LogCard,
		QFrame#PreviewCard {
			background-color: #e8e4dd;
			border: 1px solid rgba(69, 88, 69, 0.16);
			border-radius: 24px;
		}
		QLabel#Eyebrow {
			color: #7c4f2c;
			font-size: 10pt;
			font-weight: 700;
			letter-spacing: 0.18em;
			text-transform: uppercase;
		}
		QLabel#HeroTitle {
			color: #193126;
			font-family: "Georgia", serif;
			font-size: 24pt;
			font-weight: 700;
		}
		QLabel#HeroBody,
		QLabel#SectionDescription,
		QLabel#LogHint,
		QLabel#StatusLabel {
			color: #536356;
			font-size: 10.5pt;
		}
		QFrame#HeroMedia {
			background-color: rgba(255, 255, 255, 0.5);
			border: 1px solid rgba(69, 88, 69, 0.12);
			border-radius: 18px;
		}
		QTabWidget::pane {
			border: 1px solid rgba(69, 88, 69, 0.16);
			background-color: rgba(255, 252, 246, 0.7);
			border-radius: 24px;
			top: -1px;
		}
		QTabBar::tab {
			background-color: #d7e4d2;
			color: #284032;
			border: 1px solid rgba(69, 88, 69, 0.18);
			padding: 14px 24px;
			min-width: 150px;
			min-height: 24px;
			margin-right: 8px;
			border-top-left-radius: 18px;
			border-top-right-radius: 18px;
			font-size: 12pt;
			font-weight: 700;
		}
		QTabBar::tab:selected {
			background-color: #f0dfc4;
			color: #193126;
		}
		QTabBar::tab:hover {
			background-color: #e4eddc;
		}
		QLabel#HeroGifFallback {
			color: #7c4f2c;
			font-size: 9.5pt;
			font-weight: 700;
		}
		QLabel#SectionTitle,
		QLabel#LogTitle,
		QLabel#PreviewTitle {
			color: #223528;
			font-family: "Georgia", serif;
			font-size: 16pt;
			font-weight: 700;
		}
		QLineEdit {
			background-color: rgba(255, 255, 255, 0.88);
			border: 1px solid rgba(69, 88, 69, 0.22);
			border-radius: 16px;
			padding: 8px 14px;
			min-height: 22px;
			selection-background-color: #c67b47;
			selection-color: #fffaf2;
		}
		QComboBox {
			background-color: rgba(255, 255, 255, 0.92);
			border: 1px solid rgba(69, 88, 69, 0.22);
			border-radius: 16px;
			padding: 8px 14px;
			padding-right: 34px;
			min-height: 22px;
		}
		QComboBox::drop-down {
			subcontrol-origin: padding;
			subcontrol-position: top right;
			width: 28px;
			border: none;
			background: transparent;
		}
		QComboBox::down-arrow {
			width: 0px;
			height: 0px;
			border-left: 6px solid transparent;
			border-right: 6px solid transparent;
			border-top: 7px solid #2f5a44;
			margin-right: 10px;
		}
		QPlainTextEdit {
			background-color: rgba(255, 255, 255, 0.88);
			border: 1px solid rgba(69, 88, 69, 0.22);
			border-radius: 16px;
			padding: 12px 14px;
			selection-background-color: #c67b47;
			selection-color: #fffaf2;
		}
		QLineEdit:focus,
		QPlainTextEdit:focus,
		QComboBox:focus {
			border: 2px solid #b86b38;
		}
		QComboBox QAbstractItemView,
		QListView,
		QTreeView,
		QMenu {
			background-color: #fffaf4;
			alternate-background-color: #f3ece2;
			color: #1f2a22;
			border: 1px solid rgba(69, 88, 69, 0.22);
			border-radius: 12px;
			outline: 0;
			selection-background-color: #b65f2d;
			selection-color: #fffaf2;
		}
		QDialog,
		QMessageBox,
		QFileDialog {
			background-color: #f7f2ea;
			color: #1f2a22;
		}
		QDialog QLabel,
		QMessageBox QLabel,
		QFileDialog QLabel {
			color: #1f2a22;
		}
		QDialog QListView,
		QDialog QTreeView,
		QFileDialog QListView,
		QFileDialog QTreeView {
			background-color: #fffaf4;
			color: #1f2a22;
			selection-background-color: #b65f2d;
			selection-color: #fffaf2;
		}
		QPushButton {
			background-color: #2f5a44;
			color: #fffaf2;
			border: none;
			border-radius: 16px;
			padding: 12px 18px;
			font-weight: 700;
		}
		QPushButton:hover {
			background-color: #376951;
		}
		QPushButton:pressed {
			background-color: #244836;
		}
		QPushButton:disabled {
			background-color: #8a9a8d;
			color: #eef2ed;
		}
		QPushButton#AccentButton {
			background-color: #b65f2d;
			font-size: 12pt;
			padding: 14px 20px;
		}
		QPushButton#AccentButton:hover {
			background-color: #c76e39;
		}
		QPushButton#AccentButton:pressed {
			background-color: #994b20;
		}
		QRadioButton {
			spacing: 10px;
			padding: 6px 0;
			color: #2b3f31;
		}
		QRadioButton::indicator {
			width: 18px;
			height: 18px;
			border-radius: 9px;
			border: 2px solid #7b8f7e;
			background-color: #fffdf9;
		}
		QRadioButton::indicator:checked {
			border: 2px solid #b65f2d;
			background-color: qradialgradient(
				cx: 0.5, cy: 0.5, radius: 0.55,
				fx: 0.5, fy: 0.5,
				stop: 0 #b65f2d,
				stop: 0.45 #b65f2d,
				stop: 0.46 #fffdf9,
				stop: 1 #fffdf9
			);
		}
	"""