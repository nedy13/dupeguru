# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from hscommon import desktop
from hscommon.trans import trget
from core import missing
from qt.file_preview_window import FilePreviewWindow

tr = trget("ui")

SORT_ROLE = Qt.ItemDataRole.UserRole
INDEX_ROLE = Qt.ItemDataRole.UserRole + 1


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
        self.preview_window = None
        self.setWindowTitle(tr("Files Missing in Reference"))
        self.resize(950, 550)
        layout = QVBoxLayout(self)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        top = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("Filter by name or folder"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.apply_filter)
        top.addWidget(self.search_edit, 1)
        self.preview_checkbox = QCheckBox(tr("Preview"))
        self.preview_checkbox.setToolTip(
            tr("Show the selected file with its attributes instead of opening the default application")
        )
        self.preview_checkbox.toggled.connect(self.preview_toggled)
        top.addWidget(self.preview_checkbox)
        layout.addLayout(top)

        self.table = QTableWidget(0, len(missing.COLUMNS))
        self.table.setHorizontalHeaderLabels([tr("Filename"), tr("Folder"), tr("Size (KB)"), tr("Modification")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.activate_selected)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.transfer_button = QPushButton(tr("Copy / Move"))
        transfer_menu = QMenu(self.transfer_button)
        for text, copy, to_reference in (
            (tr("Copy Selected to Reference..."), True, True),
            (tr("Move Selected to Reference..."), False, True),
            (tr("Copy Selected to Folder..."), True, False),
            (tr("Move Selected to Folder..."), False, False),
        ):
            action = QAction(text, transfer_menu)
            action.triggered.connect(lambda checked=False, c=copy, r=to_reference: self.transfer_selected(c, r))
            transfer_menu.addAction(action)
        self.transfer_button.setMenu(transfer_menu)
        self.export_button = QPushButton(tr("Export to CSV"))
        self.export_button.clicked.connect(self.export_csv)
        self.open_button = QPushButton(tr("Open Selected with Default Application"))
        self.open_button.clicked.connect(self.open_selected)
        self.reveal_button = QPushButton(tr("Open Containing Folder of Selected"))
        self.reveal_button.clicked.connect(self.reveal_selected)
        close_button = QPushButton(tr("Close"))
        close_button.clicked.connect(self.close)
        self.file_buttons = (self.transfer_button, self.export_button, self.open_button, self.reveal_button)
        for button in self.file_buttons:
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    # --- List
    def refresh(self):
        files = self.app.model.missing_in_reference
        self.files = list(files or [])
        self.no_reference = files is None
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(self.files))
        for row, f in enumerate(self.files):
            # Inside a folder, files are sorted by name
            raw_values = [f.name.lower(), f"{str(f.folder_path).lower()}\0{f.name.lower()}", f.size, f.mtime]
            for column, (text, raw) in enumerate(zip(missing.file_row(f), raw_values)):
                item = SortableItem(text)
                item.setData(SORT_ROLE, raw)
                # Keeps the link to the file whatever the sorting is
                item.setData(INDEX_ROLE, row)
                if column == 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, column, item)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        for column in (0, 2, 3):
            self.table.resizeColumnToContents(column)
        for button in self.file_buttons:
            button.setEnabled(bool(self.files))
        self.apply_filter()

    def apply_filter(self):
        text = self.search_edit.text().strip().lower()
        shown = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            f = self.files[item.data(INDEX_ROLE)]
            visible = not text or text in f.name.lower() or text in str(f.folder_path).lower()
            self.table.setRowHidden(row, not visible)
            shown += visible
        self._update_summary(shown)

    def _update_summary(self, shown):
        if self.no_reference:
            self.summary_label.setText(
                tr(
                    "Scan with at least one folder set to the Reference state first. Files of the normal folders "
                    "without a duplicate in the reference folders are listed here. Saved results don't contain "
                    "this information."
                )
            )
            return
        text = tr("%d files of the normal folders have no duplicate in the reference folders.") % len(self.files)
        if shown != len(self.files):
            text += " " + tr("%d shown.") % shown
        self.summary_label.setText(text)

    def show(self):
        self.refresh()
        super().show()
        self.raise_()
        self.activateWindow()

    def visible_files(self):
        rows = [row for row in range(self.table.rowCount()) if not self.table.isRowHidden(row)]
        return [self.files[self.table.item(row, 0).data(INDEX_ROLE)] for row in rows]

    def selected_files(self):
        rows = {index.row() for index in self.table.selectionModel().selectedRows()}
        rows = [row for row in sorted(rows) if not self.table.isRowHidden(row)]
        return [self.files[self.table.item(row, 0).data(INDEX_ROLE)] for row in rows]

    # --- Preview
    def preview_toggled(self, checked):
        if checked:
            self.selection_changed()
        elif self.preview_window is not None:
            self.preview_window.close()

    def selection_changed(self):
        if not self.preview_checkbox.isChecked():
            return
        selected = self.selected_files()
        if selected:
            self.show_preview(selected[0])

    def show_preview(self, f):
        if self.preview_window is None:
            self.preview_window = FilePreviewWindow(self)
        self.preview_window.show_file(f.path)

    # --- Actions
    def activate_selected(self):
        if self.preview_checkbox.isChecked():
            selected = self.selected_files()
            if selected:
                self.show_preview(selected[0])
        else:
            self.open_selected()

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
            # Exports what is shown, the filter applies
            missing.export_to_csv(self.visible_files(), destination)
        except OSError as e:
            QMessageBox.warning(self, tr("Export to CSV"), str(e))

    def _choose_reference_folder(self):
        folders = missing.reference_folders(self.app.model.directories)
        if not folders:
            QMessageBox.information(self, self.windowTitle(), tr("There is no folder in the Reference state."))
            return None
        if len(folders) == 1:
            return folders[0]
        names = [str(folder) for folder in folders]
        name, ok = QInputDialog.getItem(self, self.windowTitle(), tr("Reference folder:"), names, 0, False)
        return folders[names.index(name)] if ok else None

    def transfer_selected(self, copy, to_reference):
        files = self.selected_files()
        if not files:
            QMessageBox.information(self, self.windowTitle(), tr("Select the files first (Ctrl+A selects all)."))
            return
        if to_reference:
            destination = self._choose_reference_folder()
        else:
            title = tr("Select a directory to copy files to") if copy else tr("Select a directory to move files to")
            destination = QFileDialog.getExistingDirectory(self, title, "", QFileDialog.Option.ShowDirsOnly) or None
        if destination is None:
            return
        if copy:
            question = tr("Copy %d files to %s, keeping their subfolders?")
        else:
            question = tr("Move %d files to %s, keeping their subfolders? They are removed from their current folder.")
        answer = QMessageBox.question(self, self.windowTitle(), question % (len(files), destination))
        if answer == QMessageBox.StandardButton.Yes:
            self.app.model.copy_or_move_missing(files, copy, destination)
