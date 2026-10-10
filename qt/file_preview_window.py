# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import QFormLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from hscommon.trans import trget
from hscommon.util import format_size
from core.pe import exif

tr = trget("ui")


def format_time(timestamp):
    return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(timestamp))


def file_attributes(path, image_size=None):
    """(label, value) pairs describing the file at ``path``."""
    stat = path.stat()
    attributes = [
        (tr("Filename"), path.name),
        (tr("Folder"), str(path.parent)),
        (tr("Kind"), path.suffix.lstrip(".").upper()),
        (tr("Size"), f"{format_size(stat.st_size, 2)} ({stat.st_size:,} bytes)"),
        (tr("Modification"), format_time(stat.st_mtime)),
    ]
    created = getattr(stat, "st_birthtime", None)
    if created:
        attributes.append((tr("Creation"), format_time(created)))
    if image_size is not None:
        attributes.append((tr("Dimensions"), f"{image_size.width()} x {image_size.height()}"))
    try:
        with path.open("rb") as fp:
            fields = exif.get_fields(fp)
    except Exception:
        fields = {}
    if fields.get("DateTimeOriginal"):
        attributes.append((tr("EXIF Timestamp"), fields["DateTimeOriginal"]))
    camera = " ".join(str(fields[key]).strip() for key in ("Make", "Model") if fields.get(key))
    if camera:
        attributes.append((tr("Camera"), camera))
    return attributes


class FilePreviewWindow(QWidget):
    """Shows a picture and the attributes of a file without opening an external application."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(tr("Preview"))
        self.resize(700, 650)
        self.pixmap = None
        layout = QVBoxLayout(self)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.image_label, 1)
        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addLayout(self.form)

    def show_file(self, path):
        reader = QImageReader(str(path))
        # Turn the picture like the camera recorded it in the EXIF orientation
        reader.setAutoTransform(True)
        image = reader.read() if reader.canRead() else None
        if image is not None and not image.isNull():
            self.pixmap = QPixmap.fromImage(image)
            image_size = image.size()
        else:
            self.pixmap = None
            image_size = None
            self.image_label.setText(tr("No preview available for this file"))
        while self.form.rowCount():
            self.form.removeRow(0)
        try:
            attributes = file_attributes(path, image_size)
        except OSError as e:
            logging.warning("Could not read '%s': %s", path, e)
            attributes = [(tr("Error"), str(e))]
        for label, value in attributes:
            value_label = QLabel(value)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setWordWrap(True)
            self.form.addRow(label + ":", value_label)
        self.setWindowTitle(tr("Preview") + f" - {path.name}")
        self._update_pixmap()
        self.show()
        self.raise_()

    def _update_pixmap(self):
        if self.pixmap is None:
            return
        scaled = self.pixmap.scaled(
            self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()
