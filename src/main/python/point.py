#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from PyQt5 import QtCore

from consts import CLOCKWISE


class Point(QtCore.QPoint):
    """
    Point of coordinates (x, y)
    """
    
    x = property(QtCore.QPoint.x, QtCore.QPoint.setX)
    y = property(QtCore.QPoint.y, QtCore.QPoint.setY)
    
    def rotate(self, center, direction=CLOCKWISE):
        """ Returns the Point image of the rotation of self
        through 90° CLOKWISE or COUNTERCLOCKWISE around center"""
        if self == center:
            return self

        p = self - center
        p = Point(-direction * p.y, direction * p.x)
        p += center
        return p

    def __add__(self, o):
        return Point(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        return Point(self.x - o.x, self.y - o.y)

    def __mul__(self, k):
        return Point(k * self.x, k * self.y)

    def __truediv__(self, k):
        return Point(self.x / k, self.y / k)

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__

    def __repr__(self):
        return "Point({}, {})".format(self.x, self.y)

    __str__ = __repr__
