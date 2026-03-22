from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMovie, QResizeEvent
from PySide6.QtWidgets import (
    QBoxLayout,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .assets import HEADER_GIF_PATH, load_app_icon
from .worker import PdfWorker


LOG_FLOAT_BREAKPOINT = 1120
LOG_FLOAT_WIDTH = 360


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UONES Name Tag Combiner")
        self.setMinimumSize(760, 680)
        self._worker: PdfWorker | None = None
        self._header_movie = None
        app_icon = load_app_icon()
        if app_icon is not None:
            self.setWindowIcon(app_icon)
        self._apply_styles()
        self._build_ui()
        self._update_content_layout(self.width())

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
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
            QFrame#LogCard {
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
            QLabel#LogHint {
                color: #536356;
                font-size: 10.5pt;
            }
            QFrame#HeroMedia {
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(69, 88, 69, 0.12);
                border-radius: 18px;
            }
            QLabel#HeroGifFallback {
                color: #7c4f2c;
                font-size: 9.5pt;
                font-weight: 700;
            }
            QLabel#SectionTitle,
            QLabel#LogTitle {
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
            }
            QPlainTextEdit {
                background-color: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(69, 88, 69, 0.22);
                border-radius: 16px;
                padding: 12px 14px;
                selection-background-color: #c67b47;
            }
            QLineEdit:focus,
            QPlainTextEdit:focus {
                border: 2px solid #b86b38;
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
        )

    def _create_section(self, title: str, description: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("SectionCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        description_label = QLabel(description)
        description_label.setObjectName("SectionDescription")
        description_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        return card, layout

    def _create_header_media(self) -> QWidget:
        media_frame = QFrame()
        media_frame.setObjectName("HeroMedia")
        media_frame.setFixedWidth(112)
        media_frame.setMinimumHeight(112)

        media_layout = QVBoxLayout(media_frame)
        media_layout.setContentsMargins(10, 10, 10, 10)
        media_layout.setSpacing(0)

        media_label = QLabel()
        media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(media_label)

        if HEADER_GIF_PATH.is_file():
            movie = QMovie(str(HEADER_GIF_PATH))
            if movie.isValid():
                movie.jumpToFrame(0)
                original_size = movie.currentPixmap().size()
                if original_size.isValid() and original_size.width() > 0:
                    target_width = 92
                    target_height = max(
                        1,
                        int(
                            original_size.height()
                            * target_width
                            / original_size.width()
                        ),
                    )
                    movie.setScaledSize(QSize(target_width, target_height))
                    media_frame.setFixedHeight(target_height + 20)
                media_label.setMovie(movie)
                movie.start()
                self._header_movie = movie
                return media_frame

        media_label.setObjectName("HeroGifFallback")
        media_label.setText("GIF\nHERE")
        return media_frame

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        content = QWidget()
        scroll_area.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 28, 28, 28)
        content_layout.setSpacing(16)

        layout.addWidget(scroll_area)

        header = QFrame()
        header.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(26, 24, 26, 24)
        header_layout.setSpacing(18)

        header_layout.addWidget(self._create_header_media(), 0, Qt.AlignmentFlag.AlignTop)

        header_text = QWidget()
        header_text_layout = QVBoxLayout(header_text)
        header_text_layout.setContentsMargins(0, 0, 0, 0)
        header_text_layout.setSpacing(8)

        eyebrow = QLabel("UONES Name Tag Combiner")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Combine a set of individual name tag images into printable A4 sheets")
        title.setObjectName("HeroTitle")
        title.setWordWrap(True)
        body = QLabel(
            "Pick an image source, choose where the PDFs should land, then export a neat stack of pages in a single pass."
        )
        body.setObjectName("HeroBody")
        body.setWordWrap(True)

        header_text_layout.addWidget(eyebrow)
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(body)
        header_layout.addWidget(header_text, 1)
        content_layout.addWidget(header)

        body = QWidget()
        self._body_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(16)
        content_layout.addWidget(body)

        form_column = QWidget()
        self._form_layout = QVBoxLayout(form_column)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        self._form_layout.setSpacing(16)
        self._body_layout.addWidget(form_column)

        input_card, input_card_layout = self._create_section(
            "Source artwork",
            "Choose the folder that holds the images you want placed into the name tag layout.",
        )
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        self._input_edit = QLineEdit()
        self._input_edit.setMinimumHeight(42)
        self._input_edit.setPlaceholderText("Select a folder containing images...")
        input_browse = QPushButton("Browse...")
        input_browse.setMinimumHeight(42)
        input_browse.clicked.connect(self._browse_input)
        input_layout.addWidget(self._input_edit)
        input_layout.addWidget(input_browse)
        input_card_layout.addLayout(input_layout)
        self._form_layout.addWidget(input_card)

        output_card, output_card_layout = self._create_section(
            "Destination",
            "Set the folder where the generated PDFs should be written.",
        )
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        self._output_edit = QLineEdit()
        self._output_edit.setMinimumHeight(42)
        self._output_edit.setPlaceholderText("Select a folder for generated PDFs...")
        output_browse = QPushButton("Browse...")
        output_browse.setMinimumHeight(42)
        output_browse.clicked.connect(self._browse_output)
        output_layout.addWidget(self._output_edit)
        output_layout.addWidget(output_browse)
        output_card_layout.addLayout(output_layout)
        self._form_layout.addWidget(output_card)

        mode_card, mode_card_layout = self._create_section(
            "Export mode",
            "Decide whether you want one combined file or a separate PDF for each finished page.",
        )
        self._radio_split = QRadioButton(
            "Split PDFs - one file per page"
        )
        self._radio_combined = QRadioButton(
            "Combined PDF - all pages in a single file"
        )
        self._radio_split.setChecked(True)
        mode_card_layout.addWidget(self._radio_split)
        mode_card_layout.addWidget(self._radio_combined)
        self._form_layout.addWidget(mode_card)

        self._generate_btn = QPushButton("Generate Print-Ready PDF")
        self._generate_btn.setObjectName("AccentButton")
        self._generate_btn.setMinimumHeight(52)
        self._generate_btn.clicked.connect(self._generate)
        self._form_layout.addWidget(self._generate_btn)
        self._form_layout.addStretch()

        self._log_card = QFrame()
        self._log_card.setObjectName("LogCard")
        self._log_card.setMinimumWidth(300)
        log_layout = QVBoxLayout(self._log_card)
        log_layout.setContentsMargins(22, 20, 22, 20)
        log_layout.setSpacing(10)

        log_title = QLabel("Activity log")
        log_title.setObjectName("LogTitle")
        log_hint = QLabel(
            "Generation status and any recoverable image errors will appear here."
        )
        log_hint.setObjectName("LogHint")
        log_hint.setWordWrap(True)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(180)
        self._log.setPlaceholderText("No activity yet.")

        log_layout.addWidget(log_title)
        log_layout.addWidget(log_hint)
        log_layout.addWidget(self._log)
        self._body_layout.addWidget(self._log_card)
        content_layout.addStretch()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._update_content_layout(event.size().width())
        super().resizeEvent(event)

    def _update_content_layout(self, width: int) -> None:
        if width >= LOG_FLOAT_BREAKPOINT:
            self._body_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self._body_layout.setStretch(0, 5)
            self._body_layout.setStretch(1, 3)
            self._log_card.setMaximumWidth(LOG_FLOAT_WIDTH)
        else:
            self._body_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self._body_layout.setStretch(0, 0)
            self._body_layout.setStretch(1, 0)
            self._log_card.setMaximumWidth(16777215)

    def _browse_input(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Select Input Images Directory"
        )
        if directory:
            self._input_edit.setText(directory)

    def _browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self._output_edit.setText(directory)

    def _append_log(self, message: str) -> None:
        self._log.appendPlainText(message)

    def _generate(self) -> None:
        image_dir = self._input_edit.text().strip()
        output_dir = self._output_edit.text().strip()

        if not image_dir:
            self._append_log("WARNING: Please select an input images directory.")
            return
        if not output_dir:
            self._append_log("WARNING: Please select an output directory.")
            return
        if not Path(image_dir).is_dir():
            self._append_log(f"WARNING: Input directory does not exist: {image_dir}")
            return
        if not Path(output_dir).is_dir():
            self._append_log(f"WARNING: Output directory does not exist: {output_dir}")
            return

        combined = self._radio_combined.isChecked()
        self._generate_btn.setEnabled(False)
        self._append_log("Starting PDF generation...")

        self._worker = PdfWorker(image_dir, output_dir, combined)
        self._worker.log_message.connect(self._append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self) -> None:
        self._append_log("Done.")
        self._generate_btn.setEnabled(True)
        self._worker = None