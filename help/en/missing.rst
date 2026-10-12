Files Missing in Reference
==========================

.. contents::

Usually, dupeGuruX is used to find files that exist twice. Sometimes, the question is the other way
around: you have a backup, a photo collection on a NAS or a sorted archive, and you want to know
whether all files from another place are in it. These files are the ones that have **no**
duplicate. This is what the **Files Missing in Reference** window shows.

Some typical cases:

* You copied the photos of your phone to your photo collection over the years, but you are not sure
  whether you got all of them before you wipe the phone.
* You have a copy of a folder on another disk and want to check that the copy is complete.
* You sorted pictures into a new folder structure and want to find the ones you forgot.

How it works
------------

Put the folder that should contain everything (the backup, the collection) in the **Reference**
state (see :doc:`folders`). Put the folders you want to check in the **Normal** state. Then, scan
as usual.

After the scan, every file of a normal folder that didn't end up in a duplicate group together
with a file of a reference folder is **missing in reference**. A few rules apply:

* All reference folders count as one reference. If you have three reference folders, a file is
  not missing as soon as it has a duplicate in any of them.
* Duplicates among the normal folders don't matter. If a file exists twice in your normal folders,
  but not in the reference, both copies are missing.
* Only matches that end up in the results count. What a duplicate is depends on the scan type and
  its options. With a low :ref:`filter hardness <filter-hardness>`, a file can have a "duplicate"
  in the reference that is only similar, and it won't be listed as missing. With a high one, a
  file that is in the reference but slightly changed is listed. Matches removed by the ignore list
  or by the "Can mix file kind" option don't count either.
* Files that aren't compared at all, because of the "Ignore files smaller than" and "Ignore files
  larger than" preferences, are never listed. dupeGuruX can't tell whether they are missing or not.
* Files that can't be read (a corrupted picture, for example) can't have a duplicate, so they are
  listed as missing.

Choosing the right scan type is the most important step. Some advice:

* To check a copy of a folder (a backup on a NAS, for example), use
  :ref:`Relative Path and Size <relative-path-scan>` in Standard mode. It doesn't read any file
  contents and is therefore very fast, even over the network.
* To be sure the contents are the same, use **Contents** in Standard mode. It reads every file,
  which takes a while for big collections.
* For pictures whose metadata (keywords, ratings, ...) might have been edited in one place but not
  the other, use :ref:`Exact Picture (ignore metadata) <exact-picture-scan>` in Picture mode.
* **Filename** is a bad choice for this task. It only compares names, wherever the files are.
  Cameras reuse names like ``IMG_1234.JPG`` or ``00001.MTS`` all the time, so a missing file is
  easily hidden by another file with the same name.

Opening the window
------------------

When there is at least one reference folder in the scan, the results window has a
**Missing in Reference** button next to **Details**. Its label shows how many files are missing.
You can also open the window through the **View** menu with **Files Missing in Reference**.

When the scan finds no duplicates at all, but some files are missing in reference, dupeGuruX asks
you whether you want to see them.

The list is kept up to date: when you copy or move files from this window, they leave the list
once they are no longer missing.

Reviewing the list
------------------

The list shows the filename, folder, size and modification time of every missing file. Click on a
column header to sort the list.

**Filter by name or folder:**
    Only show the files whose name or folder contains what you type. The filter isn't case
    sensitive. The text above the list tells you how many files are shown.
**Preview:**
    When this box is checked, selecting a file shows it in a preview window, with its attributes
    (size, dates, dimensions, and for photos the EXIF timestamp and camera). This is much faster
    than opening every file with another application. In the preview window, the arrow keys and
    Page Up/Page Down go to the previous or next file of the list, **space** checks or unchecks the
    current file and **Escape** closes the window.
**Open Selected with Default Application:**
    Open the selected files with the application associated with their type. Double-clicking on a
    file does the same, or shows it in the preview when the **Preview** box is checked.
**Open Containing Folder of Selected:**
    Open the folder containing the selected files.

Checking files
--------------

Every file has a check box. Checked files are the files the **Copy / Move** and **Export to CSV**
actions work on. You can check a file by clicking on its box, or by selecting it and pressing
**space** (also in the preview window). The **Check** button has a menu to check all shown files,
uncheck all files or invert the checks of the shown files. Combined with the filter, this lets you
check, for example, all files of a given folder in a few clicks.

When no file is checked, **Copy / Move** works on the selected files instead.

Copying or moving the missing files
-----------------------------------

The **Copy / Move** button has four actions:

**Copy to Reference... / Move to Reference...:**
    Copy or move the files into a reference folder. If there is more than one reference folder in
    your folder list, you are asked which one to use.
**Copy to Folder... / Move to Folder...:**
    Copy or move the files to a folder you choose.

In all cases, dupeGuruX re-creates the subfolders of the file below the folder it comes from. For
example, if you scanned ``/home/me/Phone`` and the reference ``/mnt/nas/Photos``, the missing file
``/home/me/Phone/2024/Holidays/IMG_1234.JPG`` is copied to ``/mnt/nas/Photos/2024/Holidays/``.
Before anything happens, dupeGuruX tells you how many files go where and asks you to confirm.

Files are never overwritten. If a file with the same name already exists in the destination, the
copy gets a number prepended to its name, such as ``[000] IMG_1234.JPG``. When moving, the
modification time of the files is kept. When copying, it's kept as well, as far as the destination
allows it.

Files copied or moved into a reference folder, and files moved anywhere, leave the list. Files
copied to another folder stay in the list, because they are still missing in the reference. When
moving, the "Remove empty folders on delete or move" preference applies to the folders the files
leave.

Exporting the list
------------------

**Export to CSV** saves the checked files, or all shown files if none is checked, to a CSV file
with their name, folder, size and modification time. You can open this file with a spreadsheet
application, or use it as a to-do list.
