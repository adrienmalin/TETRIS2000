# -*- coding: utf-8 -*-


import sys
import os

try:
    from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia
except ImportError as pyqt5_error:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui, QtMultimedia
    except ImportError as pyside2_error:
        sys.exit(
            "This program require a Qt5 library.\n"
            "You can install PyQt5 (recommended) :\n"
            "    pip3 install --user PyQt5\n"
            "    pip3 install --user qdarkstyle\n"
            "or PySide2 :\n"
            "    pip3 install --user PySide2\n"
            + pyqt5_error.msg
            + "\n"
            + pyside2_error.msg
        )
    else:
        os.environ["QT_API"] = "pyside2"
else:
    os.environ["QT_API"] = "pyqt5"
    QtCore.Signal = QtCore.pyqtSignal
