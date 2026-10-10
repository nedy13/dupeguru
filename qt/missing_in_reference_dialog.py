# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from hscommon import desktop
from hscommon.trans import trget
from core import missing

tr = trget("ui")

SORT_ROLE = Qt.ItemDataRole.UserRole


class SortableItem(QTableWidgetItem):
    """Item sorted by the raw value stored in SORT_ROLE (size, timestamp) instead of the displayed text."""

    def __lt__(self, other):
        return self.data(SORT_ROLE) < other.data(SORT_ROLE)


class MissingInReferenceDialog(QDialog):
    """Lists the files of the normal folders that have no duplicate in the reference folders."""

    def __init__(self, app, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.app = app
        self.files = []
        self.setWindowTitle(tr("Files Missing in Reference"))
        self.resize(900, 500)
        layout = QVBoxLayout(self)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self.table = QTableWidget(0, len(missing.COLUMNS))
        self.table.setHorizontalHeaderLabels([tr("Filename"), tr("Folder"), tr("Size (KB)"), tr("Modification")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.open_selected)
        layout.addWidget(self.table)
        buttons = QHBoxLayout()
        self.export_button = QPushButton(tr("Export to CSV"))
        self.export_button.clicked.connect(self.export_csv)
        self.open_button = QPushButton(tr("Open Selected with Default Application"))
        self.open_button.clicked.connect(self.open_selected)
        self.reveal_button = QPushButton(tr("Open Containing Folder of Selected"))
        self.reveal_button.clicked.connect(self.reveal_selected)
        close_button = QPushButton(tr("Close"))
        close_button.clicked.connect(self.close)
        for button in (self.export_button, self.open_button, self.reveal_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def refresh(self):
        files = self.app.model.missing_in_reference
        self.files = files or []
        if files is None:
            self.summary_label.setText(
                tr(
                    "Scan with at least one folder set to the Reference state first. Files of the normal folders "
                    "without a duplicate in the reference folders are listed here. Saved results don't contain "
                    "this information."
                )
            )
        else:
            self.summary_label.setText(
                tr("%d files of the normal folders have no duplicate in the reference folders.") % len(files)
            )
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.files))
        for row, f in enumerate(self.files):
            raw_values = [f.name.lower(), str(f.folder_path).lower(), f.size, f.mtime]
            for column, (text, raw) in enumerate(zip(missing.file_row(f), raw_values)):
                item = SortableItem(text)
                item.setData(SORT_ROLE, raw)
                if column == 0:
                    # Keeps the link to the file whatever the sorting is
                    item.setData(SORT_ROLE + 1, row)
                if column == 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, column, item)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.table.resizeColumnToContents(0)
        for button in (self.export_button, self.open_button, self.reveal_button):
            button.setEnabled(bool(self.files))

    def show(self):
        self.refresh()
        super().show()
        self.raise_()
        self.activateWindow()

    def selected_files(self):
        rows = {index.row() for index in self.table.selectionModel().selectedRows()}
        return [self.files[self.table.item(row, 0).data(SORT_ROLE + 1)] for row in sorted(rows)]

    def open_selected(self):
        for f in self.selected_files():
            desktop.open_path(f.path)

    def reveal_selected(self):
        for f in self.selected_files():
            desktop.reveal_path(f.path)

    def export_csv(self):
        title = tr("Select a file to save your results to")
        files_filter = tr("CSV Files (*.csv)")
        destination, _ = QFileDialog.getSaveFileName(self, title, "missing_in_reference.csv", files_filter)
        if not destination:
            return
        try:
            missing.export_to_csv(self.files, destination)
        except OSError as e:
            QMessageBox.warning(self, tr("Export to CSV"), str(e))
