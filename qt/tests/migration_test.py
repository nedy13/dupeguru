# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import os.path as op

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication  # noqa: E402

from qt import util  # noqa: E402


@pytest.fixture
def paths(tmp_path, monkeypatch):
    # Settings file and data folder of each application name, as Qt would derive them
    def settings_and_data_paths():
        name = QCoreApplication.applicationName()
        return str(tmp_path / "config" / f"{name}.conf"), str(tmp_path / "data" / name)

    monkeypatch.setattr(util, "_settings_and_data_paths", settings_and_data_paths)
    monkeypatch.setattr(util, "executable_folder", lambda: str(tmp_path / "exe"))
    former_name = QCoreApplication.applicationName()
    QCoreApplication.setApplicationName("dupeGuruX")
    yield tmp_path
    QCoreApplication.setApplicationName(former_name)


def make_former_files(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "dupeGuru.conf").write_text("[General]\nLanguage=de\n")
    (tmp_path / "data" / "dupeGuru").mkdir(parents=True)
    (tmp_path / "data" / "dupeGuru" / "last_directories.xml").write_text("<directories/>")


def test_takes_over_settings_and_data(paths):
    make_former_files(paths)
    util.migrate_from_former_name()
    assert (paths / "config" / "dupeGuruX.conf").read_text() == "[General]\nLanguage=de\n"
    assert (paths / "data" / "dupeGuruX" / "last_directories.xml").read_text() == "<directories/>"
    # Copied, so that dupeGuru keeps working
    assert (paths / "config" / "dupeGuru.conf").exists()
    assert (paths / "data" / "dupeGuru" / "last_directories.xml").exists()
    assert QCoreApplication.applicationName() == "dupeGuruX"


def test_keeps_existing_files(paths):
    make_former_files(paths)
    (paths / "data" / "dupeGuruX").mkdir(parents=True)
    util.migrate_from_former_name()
    assert not (paths / "config" / "dupeGuruX.conf").exists()
    assert not (paths / "data" / "dupeGuruX" / "last_directories.xml").exists()


def test_nothing_to_take_over(paths):
    util.migrate_from_former_name()
    assert not op.exists(paths / "config" / "dupeGuruX.conf")
    assert not op.exists(paths / "data" / "dupeGuruX")


def test_portable_installation_is_left_alone(paths):
    make_former_files(paths)
    (paths / "exe").mkdir()
    (paths / "exe" / "settings.ini").write_text("")
    util.migrate_from_former_name()
    assert not (paths / "data" / "dupeGuruX").exists()


def test_portable_mode_keeps_user_files_next_to_the_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(util, "executable_folder", lambda: str(tmp_path))
    assert not util.is_portable()
    (tmp_path / "settings.ini").write_text("")
    assert util.is_portable()
    assert util.get_appdata(util.is_portable()) == str(tmp_path / "data")
