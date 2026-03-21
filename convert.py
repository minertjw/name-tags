import os
from pathlib import Path
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

def convert_heic_to_jpg(directory, quality=90):
    directory = Path(directory)
    for file in directory.glob("*.heic"):
        try:
            with Image.open(file) as img:
                out_path = file.with_suffix('.jpg')
                img.save(out_path, "JPEG", quality=quality)
                print(f"Converted: {file} -> {out_path}")
        except Exception as e:
            print(f"Failed to convert {file}: {e}")

if __name__ == "__main__":
    convert_heic_to_jpg("C:/Users/thomas/OneDrive/Pictures/DTS Slideshow")