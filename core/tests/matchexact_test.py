# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import sqlite3

import pytest

from core import fs
from core.fs import FilesDB, hasher
from core.pe import matchexact
from core.pe.photo import Photo
from core.pe.scanner import ScannerPE
from core.scanner import ScanType


class FakePhoto(Photo):
    """File content "metadata|pixels", the digest ignores the metadata. Module level for worker processes."""

    def _plat_get_pixel_digest(self):
        content = self.path.read_bytes()
        if content == b"broken":
            raise OSError(f"cannot decode {self.path}")
        return hasher(content.split(b"|", 1)[-1]).digest()


@pytest.fixture
def cache(monkeypatch):
    stored = {}
    monkeypatch.setattr(fs.filesdb, "get", lambda path, key: stored.get((str(path), key)))
    monkeypatch.setattr(fs.filesdb, "put", lambda path, key, value: stored.__setitem__((str(path), key), value))
    return stored


def make(tmp_path, name, content, is_ref=False):
    path = tmp_path / name
    path.write_bytes(content)
    picture = FakePhoto(path)
    picture.is_ref = is_ref
    return picture


def pairs(matches):
    return sorted(tuple(sorted((m.first.name, m.second.name))) for m in matches)


@pytest.mark.parametrize("parallel", [False, True])
def test_identical_pixels_match_whatever_the_metadata(tmp_path, cache, parallel):
    pictures = [
        make(tmp_path, "ref.jpg", b"camera A|pixels 1", is_ref=True),
        make(tmp_path, "tagged.jpg", b"keywords, rating|pixels 1"),
        make(tmp_path, "other.jpg", b"camera A|pixels 2"),
        make(tmp_path, "broken.jpg", b"broken"),
    ]
    matches = matchexact.getmatches(pictures, parallel=parallel)
    assert pairs(matches) == [("ref.jpg", "tagged.jpg")]
    assert all(m.percentage == 100 for m in matches)


def test_reference_pictures_are_not_compared_to_each_other(tmp_path, cache):
    pictures = [
        make(tmp_path, "ref1.jpg", b"a|same", is_ref=True),
        make(tmp_path, "ref2.jpg", b"b|same", is_ref=True),
        make(tmp_path, "normal.jpg", b"c|same"),
    ]
    assert pairs(matchexact.getmatches(pictures)) == [("normal.jpg", "ref1.jpg"), ("normal.jpg", "ref2.jpg")]


def test_parallel_and_sequential_digests_are_equal(tmp_path, cache):
    pictures = [make(tmp_path, f"p{i}.jpg", f"meta {i}|pixels {i % 7}".encode()) for i in range(60)]
    sequential = matchexact.get_pixel_digests(pictures, parallel=False)
    cache.clear()
    parallel = matchexact.get_pixel_digests([FakePhoto(p.path) for p in pictures], parallel=True)
    assert sorted(sequential.values()) == sorted(parallel.values())


def test_cached_digests_are_used(tmp_path, cache, monkeypatch):
    pictures = [make(tmp_path, "a.jpg", b"x|pixels"), make(tmp_path, "b.jpg", b"y|pixels")]
    matchexact.get_pixel_digests(pictures, parallel=False)

    def fail(self):
        raise OSError("decoded again")

    monkeypatch.setattr(FakePhoto, "_plat_get_pixel_digest", fail)
    again = [FakePhoto(p.path) for p in pictures]
    for picture in again:
        picture.is_ref = False
    assert pairs(matchexact.getmatches(again, parallel=False)) == [("a.jpg", "b.jpg")]


def test_scanner_and_missing_in_reference(tmp_path, cache):
    pictures = [
        make(tmp_path, "ref.jpg", b"original|pixels 1", is_ref=True),
        make(tmp_path, "tagged.jpg", b"edited tags|pixels 1"),
        make(tmp_path, "new.jpg", b"original|pixels 3"),
    ]
    scanner = ScannerPE()
    scanner.scan_type = ScanType.EXACTPICTURE
    groups = scanner.get_dupe_groups(pictures)
    assert len(groups) == 1 and groups[0].ref.name == "ref.jpg"
    assert [p.name for p in scanner.missing_in_reference] == ["new.jpg"]


def test_files_db_upgrade_keeps_digests(tmp_path):
    path = tmp_path / "hash_cache.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE schema_version (version int PRIMARY KEY, description TEXT)")
    conn.execute("INSERT INTO schema_version VALUES (1, 'Changed from md5 to xxhash if available.')")
    conn.execute(
        """CREATE TABLE files (path TEXT PRIMARY KEY, size INTEGER, mtime_ns INTEGER,
        entry_dt DATETIME, digest BLOB, digest_partial BLOB, digest_samples BLOB)"""
    )
    conn.execute("INSERT INTO files (path, size, mtime_ns, digest) VALUES ('/x.jpg', 1, 2, x'abcd')")
    conn.commit()
    conn.close()
    db = FilesDB()
    db.connect(path)
    with db.conn as conn:
        assert conn.execute("SELECT digest, pixel_digest FROM files").fetchall() == [(b"\xab\xcd", None)]
        assert conn.execute("SELECT max(version) FROM schema_version").fetchone()[0] == 2
    db.close()
