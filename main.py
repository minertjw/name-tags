import os
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QApplication, QFileDialog, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QPlainTextEdit, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)
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
        self.setWindowTitle("Name Tag PDF Generator")
        self.setMinimumWidth(600)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        # Input directory row
        input_group = QGroupBox("Input Images Directory")
        input_layout = QHBoxLayout(input_group)
        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText("Select a folder containing images…")
        input_browse = QPushButton("Browse…")
        input_browse.clicked.connect(self._browse_input)
        input_layout.addWidget(self._input_edit)
        input_layout.addWidget(input_browse)
        layout.addWidget(input_group)

        # Output directory row
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout(output_group)
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Select a folder for generated PDFs…")
        output_browse = QPushButton("Browse…")
        output_browse.clicked.connect(self._browse_output)
        output_layout.addWidget(self._output_edit)
        output_layout.addWidget(output_browse)
        layout.addWidget(output_group)

        # Output mode selection
        mode_group = QGroupBox("Output Mode")
        mode_layout = QVBoxLayout(mode_group)
        self._radio_split = QRadioButton("Split PDFs — one file per page (current behavior)")
        self._radio_combined = QRadioButton("Combined PDF — all pages in a single file")
        self._radio_split.setChecked(True)
        mode_layout.addWidget(self._radio_split)
        mode_layout.addWidget(self._radio_combined)
        layout.addWidget(mode_group)

        # Generate button
        self._generate_btn = QPushButton("Generate PDF")
        self._generate_btn.setFixedHeight(36)
        self._generate_btn.clicked.connect(self._generate)
        layout.addWidget(self._generate_btn)

        # Log area
        log_label = QLabel("Log:")
        layout.addWidget(log_label)
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(150)
        layout.addWidget(self._log)

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
