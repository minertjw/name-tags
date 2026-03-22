from PySide6.QtCore import QThread, Signal

from .pdf import generate_combined_pdf, generate_split_pdfs


class PdfWorker(QThread):
    log_message = Signal(str)
    finished = Signal()

    def __init__(self, image_dir: str, output_dir: str, combined: bool):
        super().__init__()
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.combined = combined

    def run(self) -> None:
        if self.combined:
            generate_combined_pdf(
                self.image_dir, self.output_dir, self.log_message.emit
            )
        else:
            generate_split_pdfs(self.image_dir, self.output_dir, self.log_message.emit)
        self.finished.emit()