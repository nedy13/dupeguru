## How to build dupeGuruX for macos
These instructions are for the Qt version of the UI on macOS.

*Note: The Cocoa UI of dupeGuru is hosted in a separate repo: https://github.com/arsenetar/dupeguru-cocoa and is no longer "supported".*
### Prerequisites

- [Python 3.12+][python]
- [Xcode 12.3][xcode] or just Xcode command line tools (older versions can be used if not interested in arm macs)
- [Homebrew][homebrew]
- [qt6](https://www.qt.io/)

#### Prerequisite setup
1. Install Xcode if desired
2. Install [Homebrew][homebrew], if not on the path after install (arm based Macs) create `~/.zshrc`
with `export PATH="/opt/homebrew/bin:$PATH"`. Will need to reload terminal or source the file to take
effect.
3. Install qt6 with `brew`. If you are using a version of macos without system python 3.12+ then you will
also need to install that via brew or with pyenv.

        $ brew install qt6

    NOTE: PySide6 ships native wheels for intel and arm macs, so installing qt6 with `brew` is
    usually not needed.

4. May need to launch a new terminal to have everything working.

### With builder.py
OSX comes with a version of python 3 by default in newer versions of OSX.
    $ cd <dupeGuruX directory>
    $ python3 -m venv ./env
    $ source ./env/bin/activate
    $ pip install -e ".[build]"
    $ python builder.py
    $ python run.py

### Generate OSX Packages
The build extras need to be installed to run packaging: `pip install -e ".[build]"`.
Run the following in the respective virtual environment.

    $ python package.py

This will produce a dupeGuruX.app in the dist folder.

### Running tests
The complete test suite can be run with tox just like on linux. NOTE: The development extras need to
be installed to run unit tests: `pip install -e ".[dev]"`.

[python]: http://www.python.org/
[homebrew]: https://brew.sh/
[xcode]: https://developer.apple.com/xcode/
