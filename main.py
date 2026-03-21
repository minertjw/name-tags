import os
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QMovie
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QPlainTextEdit, QPushButton, QRadioButton,
                               QScrollArea, QVBoxLayout, QWidget)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# === Layout Constants ===
IMAGES_PER_PAGE = 8
IMAGE_WIDTH_CM = 9.2
MARGIN_CM = 1
COLUMNS = 2
ROWS = 4
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')

page_width, page_height = A4
usable_width = page_width - 2 * MARGIN_CM * cm
usable_height = page_height - 2 * MARGIN_CM * cm
x_spacing = (usable_width - COLUMNS * IMAGE_WIDTH_CM * cm) / (COLUMNS - 1)
image_width_px = IMAGE_WIDTH_CM * cm
BASE_DIR = Path(__file__).resolve().parent
ICON_PATHS = (
    BASE_DIR / "assets" / "app_icon.ico",
    BASE_DIR / "assets" / "app_icon.png",
)
HEADER_GIF_PATH = BASE_DIR / "assets" / "header_animation.gif"


def load_app_icon() -> QIcon | None:
    for icon_path in ICON_PATHS:
        if icon_path.is_file():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                return icon
    return None


def collect_images(image_dir: str) -> list[str]:
    return sorted([
        f for f in os.listdir(image_dir)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    ])


def draw_image(c: canvas.Canvas, img_path: Path, x: float, y: float) -> None:
    try:
        with Image.open(img_path) as img:
            aspect = img.height / img.width
            img_height_px = image_width_px * aspect
            c.drawImage(str(img_path), x, y, width=image_width_px, height=img_height_px, preserveAspectRatio=True)
    except Exception as e:
        raise RuntimeError(f"Failed to draw {img_path}: {e}") from e


def generate_split_pdfs(image_dir: str, output_dir: str, log) -> None:
    """Generate one PDF file per batch of images_per_page images."""
    images = collect_images(image_dir)
    if not images:
        log(f"⚠️ No images found in {image_dir}")
        return

    for batch_index in range(0, len(images), IMAGES_PER_PAGE):
        batch_images = images[batch_index:batch_index + IMAGES_PER_PAGE]
        output_pdf = str(Path(output_dir) / f"output_batch_{batch_index // IMAGES_PER_PAGE + 1}.pdf")
        c = canvas.Canvas(output_pdf, pagesize=A4)

        for i, img_name in enumerate(batch_images):
            if i % IMAGES_PER_PAGE == 0 and i != 0:
                c.showPage()

            col = (i % IMAGES_PER_PAGE) % COLUMNS
            row = (i % IMAGES_PER_PAGE) // COLUMNS
            x = MARGIN_CM * cm + col * (image_width_px + x_spacing)
            y = page_height - MARGIN_CM * cm - (row + 1) * (usable_height / ROWS)

            img_path = Path(image_dir) / img_name
            try:
                draw_image(c, img_path, x, y)
            except RuntimeError as e:
                log(f"⚠️ {e}")

        c.save()
        log(f"PDF saved: {output_pdf}")


def generate_combined_pdf(image_dir: str, output_dir: str, log) -> None:
    """Generate a single combined PDF containing all images."""
    images = collect_images(image_dir)
    if not images:
        log(f"⚠️ No images found in {image_dir}")
        return

    output_pdf = str(Path(output_dir) / "output_combined.pdf")
    c = canvas.Canvas(output_pdf, pagesize=A4)

    for i, img_name in enumerate(images):
        if i % IMAGES_PER_PAGE == 0 and i != 0:
            c.showPage()

        col = (i % IMAGES_PER_PAGE) % COLUMNS
        row = (i % IMAGES_PER_PAGE) // COLUMNS
        x = MARGIN_CM * cm + col * (image_width_px + x_spacing)
        y = page_height - MARGIN_CM * cm - (row + 1) * (usable_height / ROWS)

        img_path = Path(image_dir) / img_name
        try:
            draw_image(c, img_path, x, y)
        except RuntimeError as e:
            log(f"⚠️ {e}")

    c.save()
    log(f"PDF saved: {output_pdf}")


# === Qt Worker Thread ===

class PdfWorker(QThread):
    log_message = Signal(str)
    finished = Signal()

    def __init__(self, image_dir: str, output_dir: str, combined: bool):
        super().__init__()
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.combined = combined

    def run(self):
        if self.combined:
            generate_combined_pdf(self.image_dir, self.output_dir, self.log_message.emit)
        else:
            generate_split_pdfs(self.image_dir, self.output_dir, self.log_message.emit)
        self.finished.emit()


# === Main Window ===

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UONES Name Tag Combiner")
        self.setMinimumSize(760, 680)
        self._worker = None
        self._header_movie = None
        app_icon = load_app_icon()
        if app_icon is not None:
            self.setWindowIcon(app_icon)
        self._apply_styles()
        self._build_ui()

    def _apply_styles(self):
        self.setStyleSheet("""
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
        """)

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
                    target_height = max(1, int(original_size.height() * target_width / original_size.width()))
                    movie.setScaledSize(QSize(target_width, target_height))
                    media_frame.setFixedHeight(target_height + 20)
                media_label.setMovie(movie)
                movie.start()
                self._header_movie = movie
                return media_frame

        media_label.setObjectName("HeroGifFallback")
        media_label.setText("GIF\nHERE")
        return media_frame

    def _build_ui(self):
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
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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

        input_card, input_card_layout = self._create_section(
            "Source artwork",
            "Choose the folder that holds the images you want placed into the name tag layout."
        )
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        self._input_edit = QLineEdit()
        self._input_edit.setMinimumHeight(42)
        self._input_edit.setPlaceholderText("Select a folder containing images…")
        input_browse = QPushButton("Browse…")
        input_browse.setMinimumHeight(42)
        input_browse.clicked.connect(self._browse_input)
        input_layout.addWidget(self._input_edit)
        input_layout.addWidget(input_browse)
        input_card_layout.addLayout(input_layout)
        content_layout.addWidget(input_card)

        output_card, output_card_layout = self._create_section(
            "Destination",
            "Set the folder where the generated PDFs should be written."
        )
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        self._output_edit = QLineEdit()
        self._output_edit.setMinimumHeight(42)
        self._output_edit.setPlaceholderText("Select a folder for generated PDFs…")
        output_browse = QPushButton("Browse…")
        output_browse.setMinimumHeight(42)
        output_browse.clicked.connect(self._browse_output)
        output_layout.addWidget(self._output_edit)
        output_layout.addWidget(output_browse)
        output_card_layout.addLayout(output_layout)
        content_layout.addWidget(output_card)

        mode_card, mode_card_layout = self._create_section(
            "Export mode",
            "Decide whether you want one combined file or a separate PDF for each finished page."
        )
        self._radio_split = QRadioButton("Split PDFs — one file per page (current behavior)")
        self._radio_combined = QRadioButton("Combined PDF — all pages in a single file")
        self._radio_split.setChecked(True)
        mode_card_layout.addWidget(self._radio_split)
        mode_card_layout.addWidget(self._radio_combined)
        content_layout.addWidget(mode_card)

        self._generate_btn = QPushButton("Generate Print-Ready PDF")
        self._generate_btn.setObjectName("AccentButton")
        self._generate_btn.setMinimumHeight(52)
        self._generate_btn.clicked.connect(self._generate)
        content_layout.addWidget(self._generate_btn)

        log_card = QFrame()
        log_card.setObjectName("LogCard")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(22, 20, 22, 20)
        log_layout.setSpacing(10)

        log_title = QLabel("Activity log")
        log_title.setObjectName("LogTitle")
        log_hint = QLabel("Generation status and any recoverable image errors will appear here.")
        log_hint.setObjectName("LogHint")
        log_hint.setWordWrap(True)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(180)
        self._log.setPlaceholderText("No activity yet.")

        log_layout.addWidget(log_title)
        log_layout.addWidget(log_hint)
        log_layout.addWidget(self._log)
        content_layout.addWidget(log_card)
        content_layout.addStretch()

    def _browse_input(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Input Images Directory")
        if directory:
            self._input_edit.setText(directory)

    def _browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self._output_edit.setText(directory)

    def _append_log(self, message: str):
        self._log.appendPlainText(message)

    def _generate(self):
        image_dir = self._input_edit.text().strip()
        output_dir = self._output_edit.text().strip()

        if not image_dir:
            self._append_log("⚠️ Please select an input images directory.")
            return
        if not output_dir:
            self._append_log("⚠️ Please select an output directory.")
            return
        if not Path(image_dir).is_dir():
            self._append_log(f"⚠️ Input directory does not exist: {image_dir}")
            return
        if not Path(output_dir).is_dir():
            self._append_log(f"⚠️ Output directory does not exist: {output_dir}")
            return

        combined = self._radio_combined.isChecked()
        self._generate_btn.setEnabled(False)
        self._append_log("Starting PDF generation…")

        self._worker = PdfWorker(image_dir, output_dir, combined)
        self._worker.log_message.connect(self._append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self):
        self._append_log("Done.")
        self._generate_btn.setEnabled(True)
        self._worker = None


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
