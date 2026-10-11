# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import os

from core import fs, matchpath
from core.scanner import ScanType
from core.se.scanner import ScannerSE


def write(path, content, mtime=1_000_000_000):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    os.utime(path, (mtime, mtime))
    return path


def files_of(tmp_path):
    """File objects of every file below ``tmp_path``, the ones below "ref" being reference files."""
    result = []
    for path in sorted(tmp_path.rglob("*")):
        if path.is_file():
            f = fs.File(path)
            f.is_ref = path.relative_to(tmp_path).parts[0] == "ref"
            result.append(f)
    return result


def relative(f, tmp_path):
    return f.path.relative_to(tmp_path).as_posix()


def pairs(matches, tmp_path):
    return sorted(tuple(sorted((relative(m.first, tmp_path), relative(m.second, tmp_path)))) for m in matches)


def test_same_relative_path_and_size_match(tmp_path):
    write(tmp_path / "ref" / "2015" / "00001.MTS", b"clip one")
    write(tmp_path / "copy" / "2015" / "00001.MTS", b"CLIP ONE", mtime=2_000_000_000)
    # Same name and size, but in another folder: not the same file
    write(tmp_path / "copy" / "video" / "00001.MTS", b"clip one")
    # Same path, other size
    write(tmp_path / "ref" / "2015" / "00002.MTS", b"clip two")
    write(tmp_path / "copy" / "2015" / "00002.MTS", b"clip two, longer")
    roots = [tmp_path / "ref", tmp_path / "copy"]
    matches = matchpath.getmatches(files_of(tmp_path), roots)
    assert pairs(matches, tmp_path) == [("copy/2015/00001.MTS", "ref/2015/00001.MTS")]
    assert matches[0].percentage == 100


def test_modification_times_within_tolerance(tmp_path):
    write(tmp_path / "ref" / "a.jpg", b"a", mtime=1_000_000_000)
    write(tmp_path / "copy" / "a.jpg", b"a", mtime=1_000_000_002)
    write(tmp_path / "ref" / "b.jpg", b"b", mtime=1_000_000_000)
    write(tmp_path / "copy" / "b.jpg", b"b", mtime=1_000_000_003)
    roots = [tmp_path / "ref", tmp_path / "copy"]
    files = files_of(tmp_path)
    assert pairs(matchpath.getmatches(files, roots, mtime_tolerance=2), tmp_path) == [("copy/a.jpg", "ref/a.jpg")]
    assert len(matchpath.getmatches(files, roots)) == 2


def test_reference_files_are_not_compared_to_each_other(tmp_path):
    (tmp_path / "ref").mkdir()
    write(tmp_path / "ref" / "one" / "a.jpg", b"a")
    write(tmp_path / "ref" / "two" / "a.jpg", b"a")
    write(tmp_path / "copy" / "a.jpg", b"a")
    roots = [tmp_path / "ref" / "one", tmp_path / "ref" / "two", tmp_path / "copy"]
    assert pairs(matchpath.getmatches(files_of(tmp_path), roots), tmp_path) == [
        ("copy/a.jpg", "ref/one/a.jpg"),
        ("copy/a.jpg", "ref/two/a.jpg"),
    ]


def test_scanner_and_missing_in_reference(tmp_path):
    write(tmp_path / "ref" / "2015" / "00001.MTS", b"clip one")
    write(tmp_path / "copy" / "2015" / "00001.MTS", b"clip one")
    # Its name exists in the reference, but not at this path: missing
    write(tmp_path / "copy" / "2016" / "00001.MTS", b"clip one")
    scanner = ScannerSE()
    scanner.scan_type = ScanType.RELATIVEPATH
    scanner.root_folders = [tmp_path / "ref", tmp_path / "copy"]
    groups = scanner.get_dupe_groups(files_of(tmp_path))
    assert len(groups) == 1
    assert relative(groups[0].ref, tmp_path) == "ref/2015/00001.MTS"
    assert [relative(f, tmp_path) for f in scanner.missing_in_reference] == ["copy/2016/00001.MTS"]


def test_app_scan_passes_root_folders(tmp_path, monkeypatch):
    from core.directories import DirectoryState
    from core.tests.base import TestApp
    from hscommon.jobprogress import job

    write(tmp_path / "ref" / "2015" / "a.jpg", b"a" * 100)
    write(tmp_path / "copy" / "2015" / "a.jpg", b"a" * 100)
    write(tmp_path / "copy" / "2015" / "new.jpg", b"n" * 100)
    app = TestApp().app
    # Run the scan in this thread
    monkeypatch.setattr(app, "_start_job", lambda jobid, func: func(job.nulljob))
    app.directories.add_path(tmp_path / "ref")
    app.directories.add_path(tmp_path / "copy")
    app.directories.set_state(tmp_path / "ref", DirectoryState.REFERENCE)
    app.options["scan_type"] = ScanType.RELATIVEPATH
    app.options["compare_mtime"] = True
    app.start_scanning()
    assert len(app.results.groups) == 1
    assert [f.name for f in app.missing_in_reference] == ["new.jpg"]
