# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import os
import random
import shutil
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QImage  # noqa: E402

from qt.pe.photo import File  # noqa: E402
from qt.tests.gui_smoke_test import dgapp, qapp, run_scan  # noqa: E402,F401


def noise_image(width=120, height=90, seed=1):
    rng = random.Random(seed)
    image = QImage(width, height, QImage.Format.Format_RGB32)
    for y in range(height):
        for x in range(width):
            image.setPixelColor(x, y, QColor(rng.randrange(256), rng.randrange(256), rng.randrange(256)))
    return image


def add_jpeg_comment(src, dst, text):
    """Insert a comment segment after the start of image marker, the picture data stays the same."""
    data = Path(src).read_bytes()
    payload = text.encode()
    segment = b"\xff\xfe" + (len(payload) + 2).to_bytes(2, "big") + payload
    Path(dst).write_bytes(data[:2] + segment + data[2:])


def digest(path):
    return File(Path(path)).get_pixel_digest()


def test_png_metadata_is_ignored(tmp_path):
    image = noise_image()
    image.save(str(tmp_path / "plain.png"))
    image.setText("Description", "Holidays, rating 5")
    image.save(str(tmp_path / "tagged.png"))
    assert (tmp_path / "plain.png").read_bytes() != (tmp_path / "tagged.png").read_bytes()
    assert digest(tmp_path / "plain.png") == digest(tmp_path / "tagged.png")


def test_jpeg_metadata_is_ignored_but_size_matters(tmp_path):
    noise_image().save(str(tmp_path / "photo.jpg"), quality=90)
    add_jpeg_comment(tmp_path / "photo.jpg", tmp_path / "commented.jpg", "Keywords: holidays")
    QImage(str(tmp_path / "photo.jpg")).scaled(60, 45).save(str(tmp_path / "small.jpg"), quality=90)
    assert digest(tmp_path / "photo.jpg") == digest(tmp_path / "commented.jpg")
    assert digest(tmp_path / "photo.jpg") != digest(tmp_path / "small.jpg")


def test_different_pictures_differ(tmp_path):
    noise_image(seed=1).save(str(tmp_path / "a.png"))
    noise_image(seed=2).save(str(tmp_path / "b.png"))
    assert digest(tmp_path / "a.png") != digest(tmp_path / "b.png")


def test_unreadable_picture_raises(tmp_path):
    (tmp_path / "broken.jpg").write_bytes(b"not a picture")
    with pytest.raises(OSError):
        digest(tmp_path / "broken.jpg")


def test_exact_picture_scan_in_app(dgapp, tmp_path):  # noqa: F811 (pytest fixture)
    from core.app import AppMode
    from core.directories import DirectoryState
    from core.scanner import ScanType

    app, errors = dgapp
    ref, normal = tmp_path / "ref", tmp_path / "normal"
    ref.mkdir()
    normal.mkdir()
    noise_image(400, 300).save(str(ref / "photo.jpg"), quality=95)
    add_jpeg_comment(ref / "photo.jpg", normal / "photo_tagged.jpg", "Rating: 5")
    QImage(str(ref / "photo.jpg")).scaled(200, 150).save(str(normal / "photo_small.jpg"), quality=95)
    shutil.copy(ref / "photo.jpg", normal / "photo_copy.jpg")
    app.directories_dialog.appModeButtonSelected(2)
    app.prefs.set_scan_type(AppMode.PICTURE, ScanType.EXACTPICTURE)
    app._update_options()
    app.model.add_directory(str(ref))
    app.model.add_directory(str(normal))
    app.model.directories.set_state(Path(ref), DirectoryState.REFERENCE)
    run_scan(app)
    groups = app.model.results.groups
    assert len(groups) == 1
    assert groups[0].ref.name == "photo.jpg"
    assert sorted(d.name for d in groups[0].dupes) == ["photo_copy.jpg", "photo_tagged.jpg"]
    assert [f.name for f in app.model.missing_in_reference] == ["photo_small.jpg"]
    assert not errors, errors
