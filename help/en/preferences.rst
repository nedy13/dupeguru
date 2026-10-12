Preferences
===========

**Tags to scan:**
    When using the **Tags** scan type, you can select the tags that will be used for comparison.

**Word weighting:**
    See :ref:`word-weighting`.

**Match similar words:**
    See :ref:`similarity-matching`.

**Match pictures of different dimensions:**
    If you check this box, pictures of different dimensions will be allowed in the same
    duplicate group.

**Match pictures of different rotations:**
    If you check this box, pictures of different rotations will be allowed in the same
    duplicate group.

    These two options are only available for the picture blocks scan. The
    :ref:`exact-picture-scan` scan type only matches pictures with the same pixels.

**Relative path scan: also compare modification times, tolerance:**
    Only available for the :ref:`relative-path-scan` scan type. When checked, two files with the
    same path and size are only duplicates if their modification times differ by at most the given
    number of seconds. The default tolerance of 2 seconds covers drives that don't store the time
    precisely (FAT, exFAT, some network drives). It's off by default because copying a file often
    changes its modification time, see :ref:`relative-path-scan` for details.

.. _filter-hardness:

**Filter Hardness:**
    The threshold needed for two files to be considered duplicates. A lower value means more
    duplicates. The meaning of the threshold depends on the scanning type (see :doc:`scan`).
    Only works for :ref:`worded <worded-scan>` and :ref:`picture blocks <picture-blocks-scan>`
    scans.

**Can mix file kind:**
    If you check this box, duplicate groups are allowed to have files with different extensions. If
    you don't check it, well, they aren't!

**Ignore duplicates hardlinking to the same file:**
    If this option is enabled, dupeGuru will verify duplicates to see if they refer to the same
    `inode`_. If they do, they will not be considered duplicates. (Only for OS X and Linux)

**Use regular expressions when filtering:**
    If you check this box, the filtering feature will treat your filter query as a
    **regular expression**. Explaining them is beyond the scope of this document. A good place to
    start learning it is `regular-expressions.info`_.

**Remove empty folders after delete or move:**
    When this option is enabled, folders are deleted after a file is deleted or moved and the folder
    is empty.

**Copy and Move:**
    Determines how the Copy and Move operations (in the Action menu) will behave.

* **Right in destination:** All files will be sent directly in the selected destination, without
  trying to recreate the source path at all.
* **Recreate relative path:** The source file's path will be re-created in the destination folder up
  to the root selection in the Directories panel. For example, if you added
  ``/Users/foobar/SomeFolder`` to your Directories panel and you move
  ``/Users/foobar/SomeFolder/SubFolder/SomeFile.ext`` to the destination
  ``/Users/foobar/MyDestination``, the final destination for the file will be
  ``/Users/foobar/MyDestination/SubFolder`` (``SomeFolder`` has been trimmed from source's path in
  the final destination.).
* **Recreate absolute path:** The source file's path will be re-created in the destination folder in
  its entirety. For example, if you move ``/Users/foobar/SomeFolder/SubFolder/SomeFile.ext`` to the
  destination ``/Users/foobar/MyDestination``, the final destination for the file will be
  ``/Users/foobar/MyDestination/Users/foobar/SomeFolder/SubFolder``.

In all cases, dupeGuru nicely handles naming conflicts by prepending a number to the destination
filename if the filename already exists in the destination.

**Custom Command:**
    This preference determines the command that will be invoked by the "Invoke Custom Command"
    action. You can invoke any external application through this action. This can be useful if,
    for example, you have a nice diffing application installed.

The format of the command is the same as what you would write in the command line, except that there
are 2 placeholders: **%d** and **%r**. These placeholders will be replaced by the path of the
selected dupe (%d) and the path of the selected dupe's reference file (%r).

If the path to your executable contains space characters, you should enclose it in "" quotes. You
should also enclose placeholders in quotes because it's very possible that paths to dupes and refs
will contain spaces. Here's an example custom command::

    "C:\Program Files\SuperDiffProg\SuperDiffProg.exe" "%d" "%r"

Advanced
--------

These options are for advanced users or for very specific situations. Most users should not have to
modify them.

**Include existence check after scan completion:**
    After the scan, check that the files of every match still exist and leave out the ones that were
    deleted or moved in the meantime. A long contents scan can take hours, and files can disappear
    during that time. This check has to look at every file again, which is slow on network drives.
    It's never done for the :ref:`relative-path-scan` scan type, which lists the files only seconds
    before.

**Ignore difference in mtime when loading cached digests:**
    The hash cache keeps the hash of every file together with its path, size and modification time.
    Normally, a file whose modification time changed is read again. With this option, a cached hash
    is used as long as the path and size are the same. Only use it if you know the contents didn't
    change, for example after a tool set new modification times on files it didn't modify.

.. _scan-workers:

**Parallel scan workers:**
    How many files are hashed and pictures analyzed at the same time. **Automatic** uses all CPU
    cores of your computer for decoding and analyzing pictures, and a few more reads than cores at
    the same time for hashing files. On computers with two cores or less, it scans single-threaded.
    Set it to **1** to always scan single-threaded, for example to keep the computer responsive
    during a long scan, or to a number to use at most that many workers. Reading many files at the
    same time is fastest on SSDs; on a single hard disk, a small number can be faster.

.. _inode: http://en.wikipedia.org/wiki/Inode
.. _regular-expressions.info: http://www.regular-expressions.info
