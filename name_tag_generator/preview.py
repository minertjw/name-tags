from email.charset import QP
from pathlib import Path
import sys

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QIntValidator, QPixmap
from PySide6.QtWidgets import (
	QApplication,
	QColorDialog,
	QFileDialog,
	QFrame,
	QFormLayout,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMainWindow,
	QPushButton,
	QScrollArea,
	QSlider,
	QVBoxLayout,
	QWidget,
)

from common.coercion import as_float, as_int, as_str
from common.styles import get_shared_stylesheet
from .settings import (
	DEFAULT_BOTTOM_FONT_SIZE,
	DEFAULT_MIDDLE_FONT_SIZE,
	DEFAULT_OUTPUT,
	DEFAULT_SHADOW_COLOR,
	DEFAULT_TOP_FONT_SIZE,
	get_default_preview_settings,
)

try:
	from .text import create_tag
except ImportError:
	from text import create_tag


BASE_DIR = Path(__file__).resolve().parent.parent


class PreviewWindow(QMainWindow):
	settingsChanged = Signal(dict)

	def __init__(self, initial_settings: dict[str, object] | None = None) -> None:
		super().__init__()
		self.setWindowTitle("Name Tag Preview")
		self.resize(1100, 760)
		self._shadow_color = QColor(DEFAULT_SHADOW_COLOR)
		self._preview_timer = QTimer(self)
		self._preview_timer.setSingleShot(True)
		self._preview_timer.setInterval(500)
		self._preview_timer.timeout.connect(self._update_preview)
		self.setStyleSheet(get_shared_stylesheet())
		self._build_ui()
		self._apply_settings(initial_settings or get_default_preview_settings())
		self._schedule_preview_refresh()

	def _build_ui(self) -> None:
		central = QWidget()
		self.setCentralWidget(central)

		layout = QHBoxLayout(central)
		layout.setContentsMargins(24, 24, 24, 24)
		layout.setSpacing(24)

		controls = QFrame()
		controls.setObjectName("SectionCard")
		controls_layout = QVBoxLayout(controls)
		controls_layout.setContentsMargins(22, 20, 22, 20)
		controls_layout.setSpacing(16)
		controls.setMaximumWidth(420)

		title = QLabel("Name tag generator")
		title.setObjectName("PreviewTitle")
		description = QLabel("Choose a template, edit the text, then update the preview to see the rendered result.")
		description.setObjectName("SectionDescription")
		description.setWordWrap(True)
		controls_layout.addWidget(title)
		controls_layout.addWidget(description)

		form = QFormLayout()
		form.setSpacing(12)

		self._template_edit = QLineEdit()
		template_browse = QPushButton("Browse...")
		template_browse.clicked.connect(self._browse_template)
		template_row = QWidget()
		template_row_layout = QHBoxLayout(template_row)
		template_row_layout.setContentsMargins(0, 0, 0, 0)
		template_row_layout.setSpacing(8)
		template_row_layout.addWidget(self._template_edit)
		template_row_layout.addWidget(template_browse)
		form.addRow("Template", template_row)

		self._top_text_edit, self._top_font_slider = self._create_text_control(
			form,
			"Top",
			"UNDERGRADUATE",
			DEFAULT_TOP_FONT_SIZE,
		)

		self._middle_text_edit, self._middle_font_slider = self._create_text_control(
			form,
			"Middle",
			"THOMAS WOOD",
			DEFAULT_MIDDLE_FONT_SIZE,
		)

		self._bottom_text_edit, self._bottom_font_slider = self._create_text_control(
			form,
			"Bottom",
			"MECHANICAL ENGINEERING",
			DEFAULT_BOTTOM_FONT_SIZE,
		)

		self._output_edit = QLineEdit(str(DEFAULT_OUTPUT))
		output_browse = QPushButton("Browse...")
		output_browse.clicked.connect(self._browse_output)
		output_row = QWidget()
		output_row_layout = QHBoxLayout(output_row)
		output_row_layout.setContentsMargins(0, 0, 0, 0)
		output_row_layout.setSpacing(8)
		output_row_layout.addWidget(self._output_edit)
		output_row_layout.addWidget(output_browse)
		form.addRow("Output", output_row)

		shadow_color_row = QWidget()
		shadow_color_layout = QHBoxLayout(shadow_color_row)
		shadow_color_layout.setContentsMargins(0, 0, 0, 0)
		shadow_color_layout.setSpacing(8)
		self._shadow_color_preview = QLabel()
		self._shadow_color_preview.setFixedSize(42, 42)
		self._shadow_color_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self._shadow_color_button = QPushButton("Choose...")
		self._shadow_color_button.clicked.connect(self._pick_shadow_color)
		shadow_color_layout.addWidget(self._shadow_color_preview)
		shadow_color_layout.addWidget(self._shadow_color_button)
		form.addRow("Shadow color", shadow_color_row)
		self._update_shadow_color_preview()

		shadow_angle_row = QWidget()
		shadow_angle_layout = QHBoxLayout(shadow_angle_row)
		shadow_angle_layout.setContentsMargins(0, 0, 0, 0)
		shadow_angle_layout.setSpacing(8)
		self._shadow_angle_slider = QSlider(Qt.Orientation.Horizontal)
		self._shadow_angle_slider.setRange(-180, 180)
		self._shadow_angle_slider.setValue(45)
		self._shadow_angle_slider.valueChanged.connect(self._update_shadow_angle_editor)
		self._shadow_angle_value = QLineEdit()
		self._shadow_angle_value.setValidator(QIntValidator(-180, 180, self))
		self._shadow_angle_value.setFixedWidth(64)
		self._shadow_angle_value.editingFinished.connect(self._apply_shadow_angle_editor)
		shadow_angle_layout.addWidget(self._shadow_angle_slider, 1)
		shadow_angle_layout.addWidget(self._shadow_angle_value)
		form.addRow("Shadow angle", shadow_angle_row)
		self._update_shadow_angle_editor(self._shadow_angle_slider.value())

		shadow_distance_row = QWidget()
		shadow_distance_layout = QHBoxLayout(shadow_distance_row)
		shadow_distance_layout.setContentsMargins(0, 0, 0, 0)
		shadow_distance_layout.setSpacing(8)
		self._shadow_distance_slider = QSlider(Qt.Orientation.Horizontal)
		self._shadow_distance_slider.setRange(0, 50)
		self._shadow_distance_slider.setValue(6)
		self._shadow_distance_slider.valueChanged.connect(self._update_shadow_distance_editor)
		self._shadow_distance_value = QLineEdit()
		self._shadow_distance_value.setValidator(QIntValidator(0, 50, self))
		self._shadow_distance_value.setFixedWidth(64)
		self._shadow_distance_value.editingFinished.connect(self._apply_shadow_distance_editor)
		shadow_distance_layout.addWidget(self._shadow_distance_slider, 1)
		shadow_distance_layout.addWidget(self._shadow_distance_value)
		form.addRow("Shadow distance", shadow_distance_row)
		self._update_shadow_distance_editor(self._shadow_distance_slider.value())

		controls_layout.addLayout(form)

		self._status = QLabel("Preview updates automatically 0.5 seconds after you stop changing values.")
		self._status.setObjectName("StatusLabel")
		self._status.setWordWrap(True)
		controls_layout.addWidget(self._status)
		controls_layout.addStretch()

		layout.addWidget(controls)

		preview_card = QFrame()
		preview_card.setObjectName("PreviewCard")
		preview_card_layout = QVBoxLayout(preview_card)
		preview_card_layout.setContentsMargins(22, 20, 22, 20)
		preview_card_layout.setSpacing(12)

		preview_title = QLabel("Preview")
		preview_title.setObjectName("PreviewTitle")
		preview_card_layout.addWidget(preview_title)

		preview_area = QScrollArea()
		preview_area.setWidgetResizable(True)
		preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self._preview_label = QLabel("No preview yet")
		self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self._preview_label.setMinimumSize(480, 640)
		preview_area.setWidget(self._preview_label)
		preview_card_layout.addWidget(preview_area)

		close_button = QPushButton("Close")
		close_button.clicked.connect(self.close)
		preview_actions = QHBoxLayout()
		preview_actions.addStretch()
		preview_actions.addWidget(close_button)
		preview_card_layout.addLayout(preview_actions)

		layout.addWidget(preview_card, 1)

		self._connect_auto_refresh()

	def _create_text_control(
		self,
		form: QFormLayout,
		label: str,
		default_text: str,
		default_font_size: int,
	) -> tuple[QLineEdit, QSlider]:
		text_edit = QLineEdit(default_text)
		text_edit.setPlaceholderText(f"Enter {label.lower()} text")
		form.addRow(f"{label} text", text_edit)

		font_row = QWidget()
		font_layout = QHBoxLayout(font_row)
		font_layout.setContentsMargins(0, 0, 0, 0)
		font_layout.setSpacing(8)
		font_slider = QSlider(Qt.Orientation.Horizontal)
		font_slider.setRange(12, 180)
		font_slider.setValue(default_font_size)
		font_value = QLineEdit(str(default_font_size))
		font_value.setValidator(QIntValidator(12, 180, self))
		font_value.setFixedWidth(64)
		font_slider.valueChanged.connect(
			lambda value, value_editor=font_value: self._update_numeric_editor(value_editor, value)
		)
		font_value.editingFinished.connect(
			lambda slider=font_slider, value_editor=font_value: self._apply_numeric_editor(
				slider,
				value_editor,
				12,
				180,
			)
		)
		font_layout.addWidget(font_slider, 1)
		font_layout.addWidget(font_value)
		form.addRow(f"{label} size", font_row)

		return text_edit, font_slider

	def _connect_auto_refresh(self) -> None:
		self._template_edit.textChanged.connect(self._schedule_preview_refresh)
		self._top_text_edit.textChanged.connect(self._schedule_preview_refresh)
		self._top_font_slider.valueChanged.connect(self._schedule_preview_refresh)
		self._middle_text_edit.textChanged.connect(self._schedule_preview_refresh)
		self._middle_font_slider.valueChanged.connect(self._schedule_preview_refresh)
		self._bottom_text_edit.textChanged.connect(self._schedule_preview_refresh)
		self._bottom_font_slider.valueChanged.connect(self._schedule_preview_refresh)
		self._output_edit.textChanged.connect(self._schedule_preview_refresh)
		self._shadow_angle_slider.valueChanged.connect(self._schedule_preview_refresh)
		self._shadow_distance_slider.valueChanged.connect(self._schedule_preview_refresh)

	def _apply_settings(self, settings: dict[str, object]) -> None:
		self._template_edit.setText(as_str(settings.get("template_path"), ""))
		self._output_edit.setText(as_str(settings.get("output_path"), str(DEFAULT_OUTPUT)))
		self._top_text_edit.setText(as_str(settings.get("top_text"), ""))
		self._middle_text_edit.setText(as_str(settings.get("middle_text"), ""))
		self._bottom_text_edit.setText(as_str(settings.get("bottom_text"), ""))
		self._top_font_slider.setValue(as_int(settings.get("top_font_size"), DEFAULT_TOP_FONT_SIZE))
		self._middle_font_slider.setValue(as_int(settings.get("middle_font_size"), DEFAULT_MIDDLE_FONT_SIZE))
		self._bottom_font_slider.setValue(as_int(settings.get("bottom_font_size"), DEFAULT_BOTTOM_FONT_SIZE))
		self._shadow_angle_slider.setValue(as_int(settings.get("shadow_angle"), 45))
		self._shadow_distance_slider.setValue(as_int(settings.get("shadow_distance"), 6))
		self._shadow_color = QColor(as_str(settings.get("shadow_color"), DEFAULT_SHADOW_COLOR))
		if not self._shadow_color.isValid():
			self._shadow_color = QColor(DEFAULT_SHADOW_COLOR)
		self._update_shadow_color_preview()

	def current_settings(self) -> dict[str, object]:
		return {
			"template_path": self._template_edit.text().strip(),
			"output_path": self._output_edit.text().strip(),
			"top_text": self._top_text_edit.text().strip(),
			"middle_text": self._middle_text_edit.text().strip(),
			"bottom_text": self._bottom_text_edit.text().strip(),
			"top_font_size": self._top_font_slider.value(),
			"middle_font_size": self._middle_font_slider.value(),
			"bottom_font_size": self._bottom_font_slider.value(),
			"shadow_color": self._shadow_color.name(),
			"shadow_angle": self._shadow_angle_slider.value(),
			"shadow_distance": self._shadow_distance_slider.value(),
		}

	def _schedule_preview_refresh(self) -> None:
		self._status.setText("Updating preview...")
		self._preview_timer.start()

	def _browse_template(self) -> None:
		selected, _ = QFileDialog.getOpenFileName(
			self,
			"Select Template Image",
			str(BASE_DIR / "images"),
			"Images (*.png *.jpg *.jpeg *.bmp *.gif)",
		)
		if selected:
			self._template_edit.setText(selected)

	def _browse_output(self) -> None:
		selected, _ = QFileDialog.getSaveFileName(
			self,
			"Select Preview Output",
			self._output_edit.text().strip() or str(DEFAULT_OUTPUT),
			"PNG Images (*.png);;JPEG Images (*.jpg *.jpeg);;BMP Images (*.bmp)",
		)
		if selected:
			self._output_edit.setText(selected)

	def _pick_shadow_color(self) -> None:
		selected = QColorDialog.getColor(self._shadow_color, self, "Select Shadow Color")
		if selected.isValid():
			self._shadow_color = selected
			self._update_shadow_color_preview()
			self._schedule_preview_refresh()

	def _update_shadow_color_preview(self) -> None:
		color_name = self._shadow_color.name()
		self._shadow_color_preview.setStyleSheet(
			f"background-color: {color_name}; border: 1px solid rgba(69, 88, 69, 0.22); border-radius: 12px;"
		)
		self._shadow_color_preview.setText("")

	def _update_numeric_editor(self, editor: QLineEdit, value: int) -> None:
		if editor.text() != str(value):
			editor.setText(str(value))

	def _apply_numeric_editor(
		self,
		slider: QSlider,
		editor: QLineEdit,
		minimum: int,
		maximum: int,
	) -> None:
		text = editor.text().strip()
		if not text:
			self._update_numeric_editor(editor, slider.value())
			return

		value = max(minimum, min(maximum, int(text)))
		slider.setValue(value)
		self._update_numeric_editor(editor, value)

	def _update_shadow_angle_editor(self, value: int) -> None:
		self._update_numeric_editor(self._shadow_angle_value, value)

	def _apply_shadow_angle_editor(self) -> None:
		self._apply_numeric_editor(self._shadow_angle_slider, self._shadow_angle_value, -180, 180)

	def _update_shadow_distance_editor(self, value: int) -> None:
		self._update_numeric_editor(self._shadow_distance_value, value)

	def _apply_shadow_distance_editor(self) -> None:
		self._apply_numeric_editor(self._shadow_distance_slider, self._shadow_distance_value, 0, 50)

	def _update_preview(self) -> None:
		settings = self.current_settings()

		try:
			rendered_path = create_tag(
				template_path=as_str(settings.get("template_path"), ""),
				top_text=as_str(settings.get("top_text"), ""),
				middle_text=as_str(settings.get("middle_text"), ""),
				bottom_text=as_str(settings.get("bottom_text"), ""),
				top_font_size=as_int(settings.get("top_font_size"), DEFAULT_TOP_FONT_SIZE),
				middle_font_size=as_int(settings.get("middle_font_size"), DEFAULT_MIDDLE_FONT_SIZE),
				bottom_font_size=as_int(settings.get("bottom_font_size"), DEFAULT_BOTTOM_FONT_SIZE),
				output_path=as_str(settings.get("output_path"), str(DEFAULT_OUTPUT)),
				shadow_color=as_str(settings.get("shadow_color"), DEFAULT_SHADOW_COLOR),
				shadow_angle=as_float(settings.get("shadow_angle"), 45.0),
				shadow_distance=as_float(settings.get("shadow_distance"), 6.0),
			)
		except Exception as exc:
			self._status.setText(str(exc))
			self._preview_label.clear()
			self._preview_label.setText("Preview unavailable")
			return

		pixmap = QPixmap(str(rendered_path))
		if pixmap.isNull():
			message = f"Failed to load preview image: {rendered_path}"
			self._status.setText(message)
			self._preview_label.clear()
			self._preview_label.setText("Preview unavailable")
			return

		scaled = pixmap.scaled(
			900,
			900,
			Qt.AspectRatioMode.KeepAspectRatio,
			Qt.TransformationMode.SmoothTransformation,
		)
		self._preview_label.setPixmap(scaled)
		self._preview_label.resize(scaled.size())
		self._status.setText(f"Preview updated: {rendered_path}")

	def closeEvent(self, event) -> None:
		self.settingsChanged.emit(self.current_settings())
		super().closeEvent(event)


def main() -> None:
	app = QApplication(sys.argv)
	window = PreviewWindow()
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()