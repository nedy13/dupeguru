# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""Files of the normal folders that have no duplicate in the reference folders."""

import csv
import os
import shutil
from pathlib import Path

from hscommon.conflict import get_conflicted_name
from hscommon.util import format_size
from core.directories import DirectoryState
from core.util import format_timestamp

COLUMNS = ["Name", "Folder", "Size", "Modification"]


def get_missing_in_reference(files, matches, has_reference=None):
    """Return the files of normal folders without any match with a file of a reference folder.

    All reference folders together form the reference. Matches between files of normal folders
    don't matter: a file missing in the reference is listed even if it is duplicated elsewhere.
    Returns ``None`` without reference, which is the case when ``has_reference`` is false or, if it
    isn't given, when ``files`` contains no file of a reference folder.
    """
    if has_reference is None:
        has_reference = any(f.is_ref for f in files)
    if not has_reference:
        return None
    in_reference = set()
    for match in matches:
        if match.first.is_ref != match.second.is_ref:
            in_reference.add(match.second if match.first.is_ref else match.first)
    return [f for f in files if not f.is_ref and f not in in_reference]


def file_row(f):
    """Display values of ``f``: name, folder, size and modification time."""
    return [f.name, str(f.folder_path), format_size(f.size, 0, 1, False), format_timestamp(f.mtime, False)]


def export_to_csv(files, dest):
    with open(dest, "w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(COLUMNS)
        for f in files:
            writer.writerow([f.name, str(f.folder_path), f.size, format_timestamp(f.mtime, False)])


def reference_folders(directories):
    """Folders in the Reference state: root folders and subfolders set to Reference."""
    folders = [path for path in directories if directories.get_state(path) == DirectoryState.REFERENCE]
    for path, state in directories.states.items():
        if state == DirectoryState.REFERENCE and path not in folders:
            folders.append(path)
    return sorted(folders)


def destination_for(f, roots, destination):
    """Path of ``f`` below ``destination``, keeping its subfolders relative to the scanned folder."""
    root = max((r for r in roots if r in f.path.parents), key=lambda r: len(r.parts), default=f.path.parent)
    return Path(destination, f.path.parent.relative_to(root), f.name)


def transfer(source, dest, copy):
    """Copy (keeping the timestamps) or move ``source`` to ``dest``, never overwriting a file.

    An existing file at ``dest`` gets the copy a "[000] " prefixed name. Returns the final path.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest = dest.parent / get_conflicted_name(os.listdir(dest.parent), dest.name)
    if copy:
        shutil.copy2(source, dest)
    else:
        shutil.move(source, dest)
    return dest
