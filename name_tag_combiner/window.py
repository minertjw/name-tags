from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMovie, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QBoxLayout,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from common.coercion import as_float, as_int, as_str
from common.styles import get_shared_stylesheet
from name_tag_generator.settings import get_default_preview_settings
from .assets import HEADER_GIF_PATH, load_app_icon
from .generator_csv import format_generator_csv_head, read_generator_csv
from .worker import PdfWorker


LOG_FLOAT_BREAKPOINT = 1120
LOG_FLOAT_WIDTH = 360

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UONES Name Tag Combiner")
        self.setMinimumSize(760, 680)
        self._worker: PdfWorker | None = None
        self._preview_window = None
        self._header_movie = None
        self._generator_settings = self._load_default_generator_settings()
        self._has_rendered_generator_preview = False
        self._generator_rows: list[dict[str, str]] = []
        self._generator_csv_path: str | None = None
        app_icon = load_app_icon()
        if app_icon is not None:
            self.setWindowIcon(app_icon)
        self._apply_styles()
        self._build_ui()
        self._update_content_layout(self.width())

    def _load_default_generator_settings(self) -> dict[str, object]:
        return get_default_preview_settings()

    def _apply_styles(self) -> None:
        self.setStyleSheet(get_shared_stylesheet())

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

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._build_generator_tab(), "Generator")
        tabs.addTab(self._build_combiner_tab(), "Combiner")
        content_layout.addWidget(tabs)
        content_layout.addStretch()

    def _build_generator_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        csv_card, csv_layout = self._create_section(
            "Imported CSV preview",
            "The first rows of the imported CSV appear here so you can verify the column mapping before generating.",
        )
        self._generator_csv_label = QLabel("No CSV imported.")
        self._generator_csv_label.setObjectName("SectionDescription")
        self._generator_csv_label.setWordWrap(True)
        self._generator_csv_head = QPlainTextEdit()
        self._generator_csv_head.setReadOnly(True)
        self._generator_csv_head.setMinimumHeight(120)
        self._generator_csv_head.setPlaceholderText("CSV head will appear here.")
        csv_layout.addWidget(self._generator_csv_label)
        csv_layout.addWidget(self._generator_csv_head)

        import_button = QPushButton("Import List To Generate")
        import_button.setMinimumHeight(46)
        import_button.clicked.connect(self._import_generator_csv)
        csv_layout.addWidget(import_button)

        settings_card, settings_layout = self._create_section(
            "Latest tag preview",
            "The latest rendered preview appears here. Use the editor to adjust template, text, and shadow settings.",
        )
        self._generator_preview_label = QLabel("No preview rendered yet.")
        self._generator_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._generator_preview_label.setMinimumHeight(320)
        self._generator_preview_label.setWordWrap(True)
        settings_layout.addWidget(self._generator_preview_label)

        preview_button = QPushButton("Edit Tag Preview")
        preview_button.setMinimumHeight(46)
        preview_button.clicked.connect(self._open_preview)
        settings_layout.addWidget(preview_button)

        self._refresh_generator_preview()

        generate_card, generate_layout = self._create_section(
            "Generate tags",
            "Use the imported CSV rows together with the current preview settings to render a full batch of tag images.",
        )
        generate_button = QPushButton("Generate Name Tags From CSV")
        generate_button.setMinimumHeight(46)
        generate_button.clicked.connect(self._generate_tags_from_csv)
        generate_layout.addWidget(generate_button)

        layout.addWidget(settings_card)
        layout.addWidget(csv_card)
        layout.addWidget(generate_card)
        layout.addStretch()
        return tab

    def _refresh_generator_preview(self) -> None:
        if not self._has_rendered_generator_preview:
            self._generator_preview_label.clear()
            self._generator_preview_label.setText("No preview rendered yet. Open Edit Tag Preview to create one.")
            return

        preview_path = Path(as_str(self._generator_settings.get("output_path"), "")).expanduser()
        if not preview_path.is_file():
            self._generator_preview_label.clear()
            self._generator_preview_label.setText("Preview has not been rendered to disk yet. Re-render it from Edit Tag Preview.")
            return

        pixmap = QPixmap(str(preview_path))
        if pixmap.isNull():
            self._generator_preview_label.clear()
            self._generator_preview_label.setText(f"Unable to load preview image:\n{preview_path}")
            return

        scaled = pixmap.scaled(
            420,
            420,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._generator_preview_label.setPixmap(scaled)
        self._generator_preview_label.resize(scaled.size())

    def _build_combiner_tab(self) -> QWidget:
        tab = QWidget()
        content_layout = QVBoxLayout(tab)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

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
        return tab

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

    def _open_preview(self) -> None:
        try:
            from name_tag_generator.preview import PreviewWindow
        except Exception as exc:
            message = f"Unable to open preview window: {exc}"
            self._append_log(message)
            QMessageBox.critical(self, "Preview Error", message)
            return

        if self._preview_window is None:
            self._preview_window = PreviewWindow(self._generator_settings)
            self._preview_window.settingsChanged.connect(self._update_generator_settings)

        self._preview_window.show()
        self._preview_window.raise_()
        self._preview_window.activateWindow()

    def _update_generator_settings(self, settings: dict[str, object]) -> None:
        self._generator_settings = dict(settings)
        self._has_rendered_generator_preview = True
        self._refresh_generator_preview()

    def _import_generator_csv(self) -> None:
        csv_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV To Generate Tags",
            str(Path.cwd()),
            "CSV Files (*.csv)",
        )
        if not csv_path:
            return

        try:
            rows = read_generator_csv(csv_path)
        except Exception as exc:
            QMessageBox.critical(self, "CSV Import Error", str(exc))
            return

        self._generator_csv_path = csv_path
        self._generator_rows = rows
        self._generator_csv_label.setText(
            f"Imported {len(rows)} rows from {csv_path}"
        )
        self._generator_csv_head.setPlainText(format_generator_csv_head(rows))
        self._refresh_generator_preview()

    def _generate_tags_from_csv(self) -> None:
        try:
            from name_tag_generator.text import create_tag
        except Exception as exc:
            QMessageBox.critical(self, "Generator Error", f"Unable to load generator: {exc}")
            return

        if not self._generator_rows:
            QMessageBox.information(
                self,
                "No CSV Imported",
                "Import a CSV with top, middle, and bottom columns first.",
            )
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory For Generated Tags",
        )
        if not output_dir:
            return

        settings = dict(self._generator_settings)
        extension = Path(as_str(settings.get("output_path"), "output.png")).suffix or ".png"

        for index, row in enumerate(self._generator_rows, start=1):
            output_path = Path(output_dir) / f"generated_tag_{index:02d}{extension}"
            create_tag(
                template_path=as_str(settings.get("template_path"), ""),
                top_text=row["top"],
                middle_text=row["middle"],
                bottom_text=row["bottom"],
                font_path=as_str(settings.get("font_path"), "").strip() or None,
                top_font_size=as_int(settings.get("top_font_size"), 64),
                middle_font_size=as_int(settings.get("middle_font_size"), 96),
                bottom_font_size=as_int(settings.get("bottom_font_size"), 64),
                bottom_horizontal_margin_cm=as_float(
                    settings.get("bottom_horizontal_margin_cm"),
                    3.0,
                ),
                output_path=output_path,
                shadow_color=as_str(settings.get("shadow_color"), "#c00000"),
                shadow_angle=as_float(settings.get("shadow_angle"), 45.0),
                shadow_distance=as_float(settings.get("shadow_distance"), 6.0),
            )

        QMessageBox.information(
            self,
            "Tags Generated",
            f"Generated {len(self._generator_rows)} name tags in {output_dir}",
        )

    def _on_finished(self) -> None:
        self._append_log("Done.")
        self._generate_btn.setEnabled(True)
        self._worker = None