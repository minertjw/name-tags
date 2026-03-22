import os
from collections.abc import Callable
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


IMAGES_PER_PAGE = 8
IMAGE_WIDTH_CM = 9.2
MARGIN_CM = 1
COLUMNS = 2
ROWS = 4
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")

page_width, page_height = A4
usable_width = page_width - 2 * MARGIN_CM * cm
usable_height = page_height - 2 * MARGIN_CM * cm
x_spacing = (usable_width - COLUMNS * IMAGE_WIDTH_CM * cm) / (COLUMNS - 1)
image_width_px = IMAGE_WIDTH_CM * cm

LogFn = Callable[[str], None]


def collect_images(image_dir: str) -> list[str]:
    return sorted(
        [f for f in os.listdir(image_dir) if f.lower().endswith(IMAGE_EXTENSIONS)]
    )


def draw_image(c: canvas.Canvas, img_path: Path, x: float, y: float) -> None:
    try:
        with Image.open(img_path) as img:
            aspect = img.height / img.width
            img_height_px = image_width_px * aspect
            c.drawImage(
                str(img_path),
                x,
                y,
                width=image_width_px,
                height=img_height_px,
                preserveAspectRatio=True,
            )
    except Exception as exc:
        raise RuntimeError(f"Failed to draw {img_path}: {exc}") from exc


def _page_position(index: int) -> tuple[float, float]:
    col = index % COLUMNS
    row = index // COLUMNS
    x = MARGIN_CM * cm + col * (image_width_px + x_spacing)
    y = page_height - MARGIN_CM * cm - (row + 1) * (usable_height / ROWS)
    return x, y


def generate_split_pdfs(image_dir: str, output_dir: str, log: LogFn) -> None:
    images = collect_images(image_dir)
    if not images:
        log(f"WARNING: No images found in {image_dir}")
        return

    for batch_index in range(0, len(images), IMAGES_PER_PAGE):
        batch_images = images[batch_index : batch_index + IMAGES_PER_PAGE]
        output_pdf = str(
            Path(output_dir)
            / f"output_batch_{batch_index // IMAGES_PER_PAGE + 1}.pdf"
        )
        c = canvas.Canvas(output_pdf, pagesize=A4)

        for image_index, img_name in enumerate(batch_images):
            x, y = _page_position(image_index)
            img_path = Path(image_dir) / img_name
            try:
                draw_image(c, img_path, x, y)
            except RuntimeError as exc:
                log(f"WARNING: {exc}")

        c.save()
        log(f"PDF saved: {output_pdf}")


def generate_combined_pdf(image_dir: str, output_dir: str, log: LogFn) -> None:
    images = collect_images(image_dir)
    if not images:
        log(f"WARNING: No images found in {image_dir}")
        return

    output_pdf = str(Path(output_dir) / "output_combined.pdf")
    c = canvas.Canvas(output_pdf, pagesize=A4)

    for image_index, img_name in enumerate(images):
        position = image_index % IMAGES_PER_PAGE
        if position == 0 and image_index != 0:
            c.showPage()

        x, y = _page_position(position)
        img_path = Path(image_dir) / img_name
        try:
            draw_image(c, img_path, x, y)
        except RuntimeError as exc:
            log(f"WARNING: {exc}")

    c.save()
    log(f"PDF saved: {output_pdf}")