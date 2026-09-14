from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, ImageFont, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from name_tag_generator.fonts import get_font_options
from name_tag_generator.settings import get_default_preview_settings, parse_render_settings
from name_tag_generator.text import create_tag

from name_tag_combiner.generator_csv import read_generator_csv_stream
from name_tag_combiner.pdf import generate_combined_pdf, generate_split_pdfs


BASE_DIR = Path(__file__).resolve().parent.parent
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_PDF_IMAGES = 500
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
FONT_SUFFIXES = {".ttf", ".otf", ".ttc"}


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES)
    if test_config:
        app.config.update(test_config)

    @app.before_request
    def require_local_request():
        host = request.host.partition(":")[0].strip("[]").lower()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            return jsonify(error="This application only accepts local requests."), 403
        origin = request.headers.get("Origin")
        if request.method != "GET" and origin:
            origin_host = (urlparse(origin).hostname or "").lower()
            if origin_host not in {"127.0.0.1", "localhost", "::1"}:
                return jsonify(error="Requests must originate from the local application."), 403

    @app.after_request
    def add_response_headers(response):
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def upload_too_large(_error):
        return jsonify(error="The upload is larger than 100 MB."), 413

    @app.get("/")
    def index():
        font_options = [
            {"id": str(index), "label": label}
            for index, (label, _value) in enumerate(get_font_options())
        ]
        return render_template(
            "index.html",
            font_options=font_options,
            defaults=get_default_preview_settings(),
        )

    @app.get("/favicon.png")
    def favicon():
        return send_file(BASE_DIR / "assets" / "app_icon.png", mimetype="image/png")

    @app.get("/header-animation.gif")
    def header_animation():
        return send_file(
            BASE_DIR / "assets" / "header_animation.gif", mimetype="image/gif"
        )

    @app.get("/norwester.otf")
    def bundled_font():
        return send_file(BASE_DIR / "assets" / "norwester.otf", mimetype="font/otf")

    @app.post("/api/csv/preview")
    def csv_preview():
        upload = request.files.get("csv")
        if upload is None or not upload.filename:
            return jsonify(error="Choose a CSV file."), 400
        if Path(upload.filename).suffix.lower() != ".csv":
            return jsonify(error="The selected file must be a CSV."), 400

        try:
            text_stream = io.TextIOWrapper(upload.stream, encoding="utf-8-sig", newline="")
            rows = read_generator_csv_stream(text_stream)
        except (UnicodeDecodeError, ValueError) as exc:
            return jsonify(error=str(exc)), 400

        return jsonify(row_count=len(rows), rows=rows[:5])

    @app.post("/api/generator/preview")
    def generator_preview():
        try:
            settings = parse_render_settings(request.form)
            with tempfile.TemporaryDirectory(prefix="name-tags-preview-") as temp_dir:
                work_dir = Path(temp_dir)
                template_path = _save_image_upload(
                    request.files.get("template"), work_dir, "template"
                )
                font_path = _resolve_font_upload(request, work_dir)
                output_path = work_dir / "preview.png"
                create_tag(
                    template_path,
                    output_path=output_path,
                    font_path=font_path,
                    **settings.create_tag_kwargs(),
                )
                content = output_path.read_bytes()
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            return jsonify(error=str(exc)), 400

        return _download(content, "preview.png", "image/png", attachment=False)

    @app.post("/api/generator/batch")
    def generator_batch():
        try:
            settings = parse_render_settings(request.form)
            rows = _read_csv_upload(request.files.get("csv"))
            with tempfile.TemporaryDirectory(prefix="name-tags-batch-") as temp_dir:
                work_dir = Path(temp_dir)
                template_path = _save_image_upload(
                    request.files.get("template"), work_dir, "template"
                )
                font_path = _resolve_font_upload(request, work_dir)
                archive_buffer = io.BytesIO()
                with zipfile.ZipFile(
                    archive_buffer, "w", compression=zipfile.ZIP_DEFLATED
                ) as archive:
                    for index, row in enumerate(rows, start=1):
                        output_name = f"generated_tag_{index:02d}.png"
                        output_path = work_dir / output_name
                        row_kwargs = settings.create_tag_kwargs()
                        row_kwargs.update(
                            top_text=row["top"],
                            middle_text=row["middle"],
                            bottom_text=row["bottom"],
                        )
                        try:
                            create_tag(
                                template_path,
                                output_path=output_path,
                                font_path=font_path,
                                **row_kwargs,
                            )
                        except (OSError, ValueError) as exc:
                            raise ValueError(f"Could not render CSV row {index}: {exc}") from exc
                        archive.write(output_path, output_name)
                content = archive_buffer.getvalue()
        except (OSError, UnicodeDecodeError, UnidentifiedImageError, ValueError) as exc:
            return jsonify(error=str(exc)), 400

        return _download(content, "generated_name_tags.zip", "application/zip")

    @app.post("/api/pdf")
    def generate_pdf():
        mode = request.form.get("mode", "split")
        if mode not in {"split", "combined"}:
            return jsonify(error="PDF mode must be split or combined."), 400

        uploads = [upload for upload in request.files.getlist("images") if upload.filename]
        if not uploads:
            return jsonify(error="Choose at least one name tag image."), 400
        if len(uploads) > MAX_PDF_IMAGES:
            return jsonify(error=f"Choose no more than {MAX_PDF_IMAGES} images."), 400

        try:
            with tempfile.TemporaryDirectory(prefix="name-tags-pdf-") as temp_dir:
                work_dir = Path(temp_dir)
                input_dir = work_dir / "images"
                output_dir = work_dir / "output"
                input_dir.mkdir()
                output_dir.mkdir()
                sorted_uploads = sorted(uploads, key=lambda upload: Path(upload.filename).name)
                for index, upload in enumerate(sorted_uploads):
                    _save_image_upload(upload, input_dir, f"{index:06d}")

                messages: list[str] = []
                if mode == "combined":
                    generate_combined_pdf(str(input_dir), str(output_dir), messages.append)
                    output_path = output_dir / "output_combined.pdf"
                    content = output_path.read_bytes()
                    filename = output_path.name
                    mimetype = "application/pdf"
                else:
                    generate_split_pdfs(str(input_dir), str(output_dir), messages.append)
                    archive_buffer = io.BytesIO()
                    with zipfile.ZipFile(
                        archive_buffer, "w", compression=zipfile.ZIP_DEFLATED
                    ) as archive:
                        for output_path in sorted(output_dir.glob("output_batch_*.pdf")):
                            archive.write(output_path, output_path.name)
                    content = archive_buffer.getvalue()
                    filename = "name_tag_pdfs.zip"
                    mimetype = "application/zip"
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            return jsonify(error=str(exc)), 400

        return _download(content, filename, mimetype)

    return app


def _read_csv_upload(upload) -> list[dict[str, str]]:
    if upload is None or not upload.filename:
        raise ValueError("Choose a CSV file.")
    if Path(upload.filename).suffix.lower() != ".csv":
        raise ValueError("The selected file must be a CSV.")
    text_stream = io.TextIOWrapper(upload.stream, encoding="utf-8-sig", newline="")
    return read_generator_csv_stream(text_stream)


def _save_image_upload(upload, directory: Path, stem: str) -> Path:
    if upload is None or not upload.filename:
        raise ValueError("Choose a template image.")
    suffix = Path(secure_filename(upload.filename)).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise ValueError("Images must be PNG, JPEG, BMP, or GIF files.")
    output_path = directory / f"{stem}{suffix}"
    upload.save(output_path)
    if output_path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Each uploaded file must be 20 MB or smaller.")
    try:
        with Image.open(output_path) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("Images must contain no more than 40 million pixels.")
            image.verify()
    except Image.DecompressionBombError as exc:
        raise ValueError("The image dimensions are too large.") from exc
    return output_path


def _resolve_font_upload(request, directory: Path) -> str | None:
    custom_font = request.files.get("custom_font")
    if custom_font is not None and custom_font.filename:
        suffix = Path(secure_filename(custom_font.filename)).suffix.lower()
        if suffix not in FONT_SUFFIXES:
            raise ValueError("Custom fonts must be TTF, OTF, or TTC files.")
        font_path = directory / f"custom-font{suffix}"
        custom_font.save(font_path)
        if font_path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("Each uploaded file must be 20 MB or smaller.")
        try:
            ImageFont.truetype(str(font_path), size=12)
        except OSError as exc:
            raise ValueError("The custom font could not be loaded.") from exc
        return str(font_path)

    font_options = get_font_options()
    font_id = request.form.get("font_id", "0")
    try:
        _label, font_path = font_options[int(font_id)]
    except (IndexError, TypeError, ValueError) as exc:
        raise ValueError("The selected font is not available.") from exc
    return font_path or None


def _download(
    content: bytes, filename: str, mimetype: str, *, attachment: bool = True
):
    return send_file(
        io.BytesIO(content),
        mimetype=mimetype,
        as_attachment=attachment,
        download_name=filename,
        max_age=0,
    )