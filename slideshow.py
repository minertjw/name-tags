import os
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white
from PIL import Image
from PIL.ExifTags import TAGS

# Register HEIC support
import pillow_heif
pillow_heif.register_heif_opener()

image_dir = 'C:/Users/thomas/OneDrive/Pictures/DTS Slideshow'
images_per_page = 1
pages_per_file = 70
images_per_file = images_per_page * pages_per_file
image_width_cm = 9.2
margin_cm = 1

page_width, page_height = landscape(A4)
usable_width = page_width - 2 * margin_cm * cm
usable_height = page_height - 2 * margin_cm * cm
image_width_px = image_width_cm * cm

# === Collect Images ===
images = sorted([
    f for f in os.listdir(image_dir)
    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.heic'))
])

def get_date_taken(img_path):
    from datetime import datetime
    try:
        with Image.open(img_path) as img:
            # For JPEG and similar formats
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                for tag, value in exif.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "DateTimeOriginal":
                        date_str = value.split(" ")[0].replace(":", "-")
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        return dt.strftime("%B %d, %Y")
            # For HEIC files
            if img.format == 'HEIF' and hasattr(img, 'info'):
                exif = img.info.get('exif', None)
                if exif:
                    import piexif
                    exif_dict = piexif.load(exif)
                    date_bytes = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
                    if date_bytes:
                        date_str = date_bytes.decode().split(" ")[0].replace(":", "-")
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        return dt.strftime("%B %d, %Y")
    except Exception as e:
        print(f"⚠️ Failed to get date from {img_path}: {e}")
    return "Unknown date"

def draw_image_and_text(c, img_path, x, y, note):
    try:
        with Image.open(img_path) as img:
            aspect = img.height / img.width
            # Reserve space for text below image
            reserved_text_height = 2.8 * cm  # Space for date and note
            max_img_height = usable_height - reserved_text_height
            # Scale image to fit within max width and max height
            img_height_px = min(max_img_height, image_width_px * aspect)
            img_width_px = min(image_width_px, img_height_px / aspect)
            # Center image horizontally and vertically (above text)
            img_x = (page_width - img_width_px) / 2
            img_y = margin_cm * cm + (max_img_height - img_height_px) / 2 + reserved_text_height
            c.drawImage(str(img_path), img_x, img_y, width=img_width_px, height=img_height_px, preserveAspectRatio=True)
            # Get date taken
            date_taken = get_date_taken(img_path)
            # Draw date and note below image
            text_y = img_y - reserved_text_height / 2
            c.setFont("Helvetica", 16)
            c.setFillColor(white)
            c.drawCentredString(page_width / 2, text_y, date_taken)
            c.setFont("Helvetica", 14)
            c.drawCentredString(page_width / 2, text_y - 1 * cm, note)
    except Exception as e:
        print(f"⚠️ Failed to draw {img_path}: {e}")

# === PDF Generation Loop ===
for batch_index in range(0, len(images), images_per_file):
    batch_images = images[batch_index:batch_index + images_per_file]
    output_pdf = f'output_batch_{batch_index // images_per_file + 1}.pdf'
    c = canvas.Canvas(output_pdf, pagesize=landscape(A4))

    for i, img_name in enumerate(batch_images):
        if i % images_per_page == 0 and i != 0:
            c.showPage()

        # Draw black background
        c.setFillColor(black)
        c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        # Center image vertically (handled in draw_image_and_text)
        img_path = Path(image_dir) / img_name

        # Prompt for note
        note = input(f"Enter note for {img_name}: ")
        if note == "skip":
            continue
        if note == "fin":
            break
        draw_image_and_text(c, img_path, 0, 0, note)

    c.save()
    print(f"✅ PDF saved: {output_pdf}")
