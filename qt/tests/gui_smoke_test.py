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

from PySide6.QtCore import QCoreApplication, QEvent  # noqa: E402
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
