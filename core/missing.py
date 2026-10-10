# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""Files of the normal folders that have no duplicate in the reference folders."""

import csv

from hscommon.util import format_size
from core.util import format_timestamp

COLUMNS = ["Name", "Folder", "Size", "Modification"]


def get_missing_in_reference(files, matches):
    """Return the files of normal folders without any match with a file of a reference folder.

    All reference folders together form the reference. Matches between files of normal folders
    don't matter: a file missing in the reference is listed even if it is duplicated elsewhere.
    Returns ``None`` when no file of a reference folder was scanned.
    """
    if not any(f.is_ref for f in files):
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
