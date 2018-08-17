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


class Propertize(type):
    def __new__(cls, name, bases, dct):
        return type.__new__(
            cls,
            name[1:],
            tuple(Propertize.this_class(base) for base in bases),
            {
                attr_name: (
                    property(attr, dct["set" + attr_name.capitalize()])
                    if "set" + attr_name.capitalize() in dct
                    else (
                        Propertize.this_class(attr)
                        if isinstance(attr, type)
                        else attr
                    )
                ) for attr_name, attr in dct.items()
            }
        )
    
    @staticmethod
    def this_class(cls):
        return Propertize(cls.__name__, cls.__bases__, cls.__dict__)
    

if __name__ == "__main__":
    class QParent:
        def __init__(self):
            self._b = 0
        def b(self):
            return self._b
        def setB(self, val):
            self._b = val
        
    
    class QTest(QParent, metaclass=Propertize):
        def __init__(self):
            super().__init__()
            self._a = 0
        def a(self):
            return self._a
        def setA(self, val):
            self._a = val
    
    
    Point = Propertize.this_class(QtCore.QPoint)()
    p = Point(1, 2)
    print(p.x, p.y)