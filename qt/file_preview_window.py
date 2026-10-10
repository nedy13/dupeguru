# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
import time

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QImageReader, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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
    """Shows a picture and the attributes of a file without opening an external application.

    The arrow keys ask for the previous or next file (``navigate``), space to check the current one
    (``toggle_requested``), whatever has the focus in the window.
    """

    navigate = Signal(int)
    toggle_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(tr("Preview"))
        self.resize(700, 650)
        # The window itself takes the focus when activated or clicked, so the keys reach its shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.pixmap = None
        self.position = ""
        self.file_name = ""
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.checked_box = QCheckBox(tr("Checked"))
        # Space is handled by the window shortcut, the box must not toggle a second time
        self.checked_box.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.checked_box.clicked.connect(lambda: self.toggle_requested.emit())
        top.addWidget(self.checked_box)
        top.addStretch(1)
        top.addWidget(QLabel(tr("Arrow keys: previous/next, Space: check")))
        layout.addLayout(top)
        shortcuts = [
            (Qt.Key.Key_Space, self.toggle_requested.emit),
            (Qt.Key.Key_Down, lambda: self.navigate.emit(1)),
            (Qt.Key.Key_Right, lambda: self.navigate.emit(1)),
            (Qt.Key.Key_PageDown, lambda: self.navigate.emit(1)),
            (Qt.Key.Key_Up, lambda: self.navigate.emit(-1)),
            (Qt.Key.Key_Left, lambda: self.navigate.emit(-1)),
            (Qt.Key.Key_PageUp, lambda: self.navigate.emit(-1)),
            (Qt.Key.Key_Escape, self.close),
        ]
        for key, func in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self, context=Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(func)
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
        self.file_name = path.name
        self._update_title()
        self._update_pixmap()
        self.show()
        self.raise_()

    def set_state(self, checked, position):
        """Show whether the current file is checked and its position, like "3/120"."""
        self.checked_box.setChecked(checked)
        self.position = position
        self._update_title()

    def _update_title(self):
        position = f" ({self.position})" if self.position else ""
        self.setWindowTitle(tr("Preview") + f" - {self.file_name}{position}")

    def _update_pixmap(self):
        if self.pixmap is None:
            return
        scaled = self.pixmap.scaled(
            self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def _take_focus(self):
        # Without a focused widget in this window, the keys would go to the list window
        focused = QApplication.focusWidget()
        if focused is None or focused.window() is not self:
            self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self._take_focus()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._take_focus()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()
