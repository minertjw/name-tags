import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from PIL import Image

# === Configuration ===
image_dir = 'images'
images_per_page = 8
pages_per_file = 1
images_per_file = images_per_page * pages_per_file
image_width_cm = 9.2
margin_cm = 1

# === Layout Constants ===
page_width, page_height = A4
usable_width = page_width - 2 * margin_cm * cm
usable_height = page_height - 2 * margin_cm * cm
columns = 2
rows = 4
x_spacing = (usable_width - columns * image_width_cm * cm) / (columns - 1)
image_width_px = image_width_cm * cm

# === Collect Images ===
images = sorted([
    f for f in os.listdir(image_dir)
    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
])

# === Drawing Function ===
def draw_image(c, img_path, x, y):
    try:
        with Image.open(img_path) as img:
            aspect = img.height / img.width
            img_height_px = image_width_px * aspect
            c.drawImage(str(img_path), x, y, width=image_width_px, height=img_height_px, preserveAspectRatio=True)
    except Exception as e:
        print(f"⚠️ Failed to draw {img_path}: {e}")

# === PDF Generation Loop ===
for batch_index in range(0, len(images), images_per_file):
    batch_images = images[batch_index:batch_index + images_per_file]
    output_pdf = f'output_batch_{batch_index // images_per_file + 1}.pdf'
    c = canvas.Canvas(output_pdf, pagesize=A4)

    for i, img_name in enumerate(batch_images):
        if i % images_per_page == 0 and i != 0:
            c.showPage()

        col = (i % images_per_page) % columns
        row = (i % images_per_page) // columns
        x = margin_cm * cm + col * (image_width_px + x_spacing)
        y = page_height - margin_cm * cm - (row + 1) * (usable_height / rows)

        img_path = Path(image_dir) / img_name
        draw_image(c, img_path, x, y)

    c.save()
    print(f"✅ PDF saved: {output_pdf}")
