# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

# Smoke tests driving the Qt UI headless. They catch API differences between Qt bindings (removed
# enums, changed return types) that only show up when a dialog is opened or a scan is run.

import os
import random
import time

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, Qt  # noqa: E402
from PySide6.QtGui import QColor, QImage  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox  # noqa: E402

from core import __appname__, __version__  # noqa: E402

# Python wrappers of the deleted widgets must outlive the test session
_keep_alive = []


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    QApplication.setApplicationName(__appname__)
    QApplication.setApplicationVersion(__version__)
    from qt import dg_rc  # noqa: F401

    return app


@pytest.fixture
def dgapp(qapp, tmp_path, monkeypatch):
    # Never block on modal dialogs and keep settings out of the user's profile
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "home" / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "home" / ".local" / "share"))
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    monkeypatch.setattr(QFileDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.StandardButton.No)
    for name in ("information", "warning", "critical"):
        monkeypatch.setattr(QMessageBox, name, staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok))
    # Answer "Yes" to confirmations such as discarding unsaved results when closing
    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    errors = []
    monkeypatch.setattr("sys.excepthook", lambda *exc_info: errors.append(exc_info))
    from qt.app import DupeGuru

    app = DupeGuru()
    # On macOS the data folder isn't moved by the environment, start without the folders of other tests
    app.model.directories.__init__()
    app.model.notify("directories_changed")
    yield app, errors
    # Let Qt delete the widgets in order, garbage collecting them later crashes PySide6
    for widget in QApplication.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    _keep_alive.append(app)


def make_files(path):
    # Noise compresses badly, which keeps the picture above the default 10 KB size threshold
    rng = random.Random(1)
    pixels = QImage(100, 100, QImage.Format.Format_RGB32)
    for y in range(100):
        for x in range(100):
            pixels.setPixelColor(x, y, QColor(rng.randrange(256), rng.randrange(256), rng.randrange(256)))
    pixels = pixels.scaled(400, 400)
    for folder in ("a", "b"):
        (path / folder).mkdir(parents=True)
        (path / folder / "same.txt").write_text("duplicate content\n" * 3000)
        pixels.save(str(path / folder / "pic.png"))


def process_events(seconds):
    end = time.time() + seconds
    while time.time() < end:
        QCoreApplication.processEvents()
        time.sleep(0.02)


def run_scan(app, timeout=60):
    progress_window = app.model.progress_window
    finished = []
    finish_func = progress_window._finish_func

    def on_finished(jobid):
        finished.append(jobid)
        finish_func(jobid)

    progress_window._finish_func = on_finished
    progress_window._error_func = lambda jobid, err: finished.append(err) or False
    app.model.start_scanning(False)
    end = time.time() + timeout
    while not finished and time.time() < end:
        process_events(0.1)
    assert finished and not isinstance(finished[0], Exception), f"scan did not finish cleanly: {finished}"
    process_events(0.2)


@pytest.mark.parametrize("mode_index, expected_groups", [(0, 2), (1, 0), (2, 1)], ids=["standard", "music", "picture"])
def test_modes(dgapp, tmp_path, mode_index, expected_groups):
    app, errors = dgapp
    make_files(tmp_path / "files")
    app.model.add_directory(str(tmp_path / "files"))
    app.directories_dialog.appModeButtonSelected(mode_index)
    app.directories_dialog.addFolderTriggered()
    app.preferencesTriggered()
    run_scan(app)
    assert len(app.model.results.groups) == expected_groups
    app.showResultsWindow()
    if app.model.results.groups:
        group = app.model.results.groups[0]
        app.model._select_dupes([group.ref, group.dupes[0]])
        app.resultWindow.actionDetails.trigger()
    process_events(0.2)
    assert not errors, errors


def test_dialogs(dgapp):
    app, errors = dgapp
    app.actionIgnoreList.trigger()
    app.actionExcludeList.trigger()
    from qt.error_report_dialog import ErrorReportDialog

    ErrorReportDialog(None, "https://example.invalid", "traceback").show()
    process_events(0.2)
    assert not errors, errors


def test_scan_type_signal_connected_once(dgapp):
    # Switching the app mode refills the scan type list, which used to add one more connection each time
    from PySide6.QtCore import SIGNAL

    app, errors = dgapp
    combo = app.directories_dialog.scanTypeComboBox
    for index in (1, 2, 0, 2, 1):
        app.directories_dialog.appModeButtonSelected(index)
    assert combo.receivers(SIGNAL("currentIndexChanged(int)")) == 1
    combo.setCurrentIndex(combo.count() - 1)
    assert not errors, errors


def test_missing_in_reference_dialog(dgapp, tmp_path, monkeypatch):
    from pathlib import Path

    from core.directories import DirectoryState
    from hscommon import desktop

    app, errors = dgapp
    ref, normal = tmp_path / "ref", tmp_path / "normal"
    ref.mkdir()
    normal.mkdir()
    # Above the default 10 KB size threshold
    (ref / "same.txt").write_text("same\n" * 5000)
    (normal / "same_copy.txt").write_text("same\n" * 5000)
    (normal / "small_missing.txt").write_text("small\n" * 3000)
    (normal / "big_missing.txt").write_text("big\n" * 9000)
    app.model.add_directory(str(ref))
    app.model.add_directory(str(normal))
    app.model.directories.set_state(Path(ref), DirectoryState.REFERENCE)
    run_scan(app)
    assert sorted(f.name for f in app.model.missing_in_reference) == ["big_missing.txt", "small_missing.txt"]

    app.actionMissingInReference.trigger()
    dialog = app.missingInReferenceDialog
    assert dialog.table.rowCount() == 2
    # Selection must follow the files when the table is sorted
    dialog.table.sortByColumn(2, Qt.SortOrder.DescendingOrder)
    dialog.table.selectRow(0)
    opened = []
    monkeypatch.setattr(desktop, "open_path", lambda path: opened.append(Path(path).name))
    dialog.open_selected()
    assert opened == ["big_missing.txt"]

    # Without reference folder there is nothing to show
    app.model.missing_in_reference = None
    dialog.refresh()
    assert dialog.table.rowCount() == 0
    assert not dialog.export_button.isEnabled()
    assert not errors, errors


def wait_for_job(app, start, timeout=60):
    """Run ``start`` launching a job of ``app`` and wait until the job finished."""
    progress_window = app.model.progress_window
    finished = []
    finish_func = progress_window._finish_func

    def on_finished(jobid):
        finish_func(jobid)
        finished.append(jobid)

    progress_window._finish_func = on_finished
    try:
        start()
        end = time.time() + timeout
        while not finished and time.time() < end:
            process_events(0.1)
    finally:
        progress_window._finish_func = finish_func
    assert finished, "job did not finish"
    process_events(0.2)


def test_missing_in_reference_actions(dgapp, tmp_path, monkeypatch):
    from pathlib import Path

    from core.directories import DirectoryState

    app, errors = dgapp
    ref, normal = tmp_path / "ref", tmp_path / "normal"
    ref.mkdir()
    (normal / "2020").mkdir(parents=True)
    (ref / "same.txt").write_text("same\n" * 5000)
    (normal / "same_copy.txt").write_text("same\n" * 5000)
    (normal / "2020" / "notes.txt").write_text("notes\n" * 3000)
    rng = random.Random(2)
    image = QImage(160, 120, QImage.Format.Format_RGB32)
    for y in range(120):
        for x in range(160):
            image.setPixelColor(x, y, QColor(rng.randrange(256), rng.randrange(256), rng.randrange(256)))
    image.save(str(normal / "2020" / "photo.png"))
    app.model.add_directory(str(ref))
    app.model.add_directory(str(normal))
    app.model.directories.set_state(Path(ref), DirectoryState.REFERENCE)
    run_scan(app)
    app.showResultsWindow()
    assert app.resultWindow.missingButton.isEnabled()
    assert app.resultWindow.missingButton.text().endswith("(2)")

    app.resultWindow.missingButton.click()
    dialog = app.missingInReferenceDialog
    dialog.search_edit.setText("PHOTO")
    assert [f.name for f in dialog.visible_files()] == ["photo.png"]

    dialog.preview_checkbox.setChecked(True)
    dialog.table.selectAll()
    preview = dialog.preview_window
    assert preview is not None and preview.isVisible()
    labels = [
        preview.form.itemAt(row, preview.form.ItemRole.LabelRole).widget().text()
        for row in range(preview.form.rowCount())
    ]
    assert "Dimensions:" in labels
    assert preview.pixmap is not None

    dialog.search_edit.clear()
    dialog.table.selectAll()
    message_parents = []
    monkeypatch.setattr(
        QMessageBox, "information", staticmethod(lambda parent, *a, **k: message_parents.append(parent))
    )
    activate(dialog)
    wait_for_job(app, lambda: dialog.transfer_selected(copy=True, to_reference=True))
    # The message after the job shows over the dialog, not in a corner of the screen
    assert message_parents == [dialog]
    assert (ref / "2020" / "photo.png").exists()
    assert (ref / "2020" / "notes.txt").exists()
    assert (normal / "2020" / "photo.png").exists()
    # Copied into the reference, nothing is missing anymore
    assert dialog.table.rowCount() == 0
    assert app.resultWindow.missingButton.text().endswith("(0)")
    assert not errors, errors


def test_no_duplicates_offers_missing_files(dgapp, tmp_path, monkeypatch):
    from pathlib import Path

    from core.directories import DirectoryState

    app, errors = dgapp
    questions = []
    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(lambda parent, title, msg, *a, **k: questions.append(msg) or QMessageBox.StandardButton.Yes),
    )
    ref, normal = tmp_path / "ref", tmp_path / "normal"
    ref.mkdir()
    normal.mkdir()
    (ref / "kept.txt").write_text("kept\n" * 5000)
    (normal / "new.txt").write_text("new\n" * 6000)
    app.model.add_directory(str(ref))
    app.model.add_directory(str(normal))
    app.model.directories.set_state(Path(ref), DirectoryState.REFERENCE)
    run_scan(app)
    assert not app.model.results.groups
    assert any("1 files of the normal folders are missing" in q for q in questions)
    assert app.missingInReferenceDialog.isVisible()
    assert app.missingInReferenceDialog.table.rowCount() == 1
    assert not errors, errors


def activate(window, timeout=5):
    """Activate ``window`` like a click of the user, the offscreen platform ignores activateWindow()."""
    window.windowHandle().requestActivate()
    end = time.time() + timeout
    while not window.isActiveWindow() and time.time() < end:
        process_events(0.05)
    assert window.isActiveWindow()
    process_events(0.05)


def test_missing_in_reference_keyboard_checks(dgapp, tmp_path, monkeypatch):
    from pathlib import Path

    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QFileDialog, QLabel

    from core import fs

    app, errors = dgapp
    files = []
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text(name)
        files.append(fs.File(Path(tmp_path / name)))
    app.model.missing_in_reference = files
    dialog = app.missingInReferenceDialog
    dialog.show()
    activate(dialog)
    dialog.table.setCurrentCell(0, 1)
    dialog.table.setFocus()
    QTest.keyClick(dialog.table, Qt.Key.Key_Space)
    assert dialog.checked_files() == [files[0]]

    dialog.preview_checkbox.setChecked(True)
    preview = dialog.preview_window
    # Like clicking into the preview: the window takes the keyboard focus from the list
    activate(preview)
    QTest.keyClick(preview, Qt.Key.Key_Down)
    assert dialog.table.currentRow() == 1
    assert preview.windowTitle().endswith("(2/3)")
    # Space checks the current file even when a label of the preview has the focus
    label = preview.findChildren(QLabel)[-1]
    label.setFocus()
    QTest.keyClick(label, Qt.Key.Key_Space)
    assert dialog.checked_files() == files[:2]
    assert preview.checked_box.isChecked()
    QTest.keyClick(preview, Qt.Key.Key_Space)
    assert dialog.checked_files() == [files[0]]
    assert not preview.checked_box.isChecked()
    QTest.keyClick(preview, Qt.Key.Key_Down)
    QTest.keyClick(preview, Qt.Key.Key_Space)

    # Copy works on the checked files only
    dest = tmp_path / "dest"
    dest.mkdir()
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *a, **k: str(dest)))
    dialog.table.selectAll()
    wait_for_job(app, lambda: dialog.transfer_selected(copy=True, to_reference=False))
    assert sorted(p.name for p in dest.iterdir()) == ["a.txt", "c.txt"]
    assert not errors, errors


QUIT_DRIVER = """
import sys
from xml.etree import ElementTree as ET

root_path, folder = sys.argv[1], sys.argv[2]
sys.path.insert(0, root_path)
from PySide6.QtCore import QCoreApplication, QStandardPaths, QTimer
from PySide6.QtWidgets import QApplication

import run
from core import __appname__

# Folders with states, saved by a previous session, are loaded on start
QCoreApplication.setOrganizationName("Hardcoded Software")
QCoreApplication.setApplicationName(__appname__)
appdata = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
import os

os.makedirs(appdata, exist_ok=True)
xml_root = ET.Element("directories")
ET.SubElement(xml_root, "root_directory").set("path", folder)
for index, name in enumerate(sorted(os.listdir(folder))):
    state = ET.SubElement(xml_root, "state")
    state.set("path", os.path.join(folder, name))
    state.set("value", str(index % 3))
ET.ElementTree(xml_root).write(os.path.join(appdata, "last_directories.xml"))


class ClosingApplication(QApplication):
    def exec(self):
        # Close the main window like clicking X does
        QTimer.singleShot(1000, lambda: [w.close() for w in QApplication.topLevelWidgets() if w.isVisible()])
        return super().exec()


run.QApplication = ClosingApplication
sys.exit(run.main())
"""


def test_quit_with_saved_folders(tmp_path):
    # Runs the real run.main() from start to shutdown with saved folders. Quitting crashed in PySide6 when
    # the garbage collector destroyed the folder tree; that was only reproducible with a real user's
    # folder list, so this covers the shutdown path but is not a reproduction of that crash.
    import subprocess
    import sys

    folder = tmp_path / "folders"
    for name in ("a", "b", "c", "d", "e", "f"):
        (folder / name / "sub").mkdir(parents=True)
    driver = tmp_path / "quit_driver.py"
    driver.write_text(QUIT_DRIVER)
    env = dict(os.environ, HOME=str(tmp_path / "home"), XDG_CONFIG_HOME=str(tmp_path / "home" / ".config"))
    env["XDG_DATA_HOME"] = str(tmp_path / "home" / ".local" / "share")
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    proc = subprocess.run(
        [sys.executable, str(driver), root_path, str(folder)], env=env, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
