#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import consts
from consts import U, D
from point import Point
from qt5 import QtCore, QtGui


class Block:
    """
    Mino or block
    Mino : A single square-shaped building block of a shape called a Tetrimino.
    Four Minos arranged into any of their various connected patterns is known as a Tetrimino
    Block : A single block locked in a cell in the Grid
    """

    # Colors
    BORDER_COLOR = consts.BLOCK_BORDER_COLOR
    FILL_COLOR = consts.BLOCK_FILL_COLOR
    GLOWING_BORDER_COLOR = consts.BLOCK_GLOWING_BORDER_COLOR 
    GLOWING_FILL_COLOR = consts.BLOCK_GLOWING_FILL_COLOR 
    LIGHT_COLOR = consts.BLOCK_LIGHT_COLOR 
    TRANSPARENT = consts.BLOCK_TRANSPARENT 
    GLOWING = consts.BLOCK_GLOWING 

    side = consts.BLOCK_INITIAL_SIDE 

    def __init__(self, coord, trail=0):
        self.coord = coord
        self.trail = trail
        self.border_color = self.BORDER_COLOR
        self.fill_color = self.FILL_COLOR
        self.glowing = self.GLOWING

    def paint(self, painter, top_left_corner, spotlight):
        p = top_left_corner + self.coord * Block.side
        block_center = Point(Block.side/2, Block.side/2)
        self.center = p + block_center
        spotlight = top_left_corner + Block.side * spotlight + block_center
        self.glint = 0.15 * spotlight + 0.85 * self.center

        if self.trail:
            start = (
                top_left_corner + (self.coord + Point(0, self.trail * U)) * Block.side
            )
            stop = top_left_corner + (self.coord + Point(0, 2 * D)) * Block.side
            fill = QtGui.QLinearGradient(start, stop)
            fill.setColorAt(0, self.LIGHT_COLOR)
            fill.setColorAt(1, self.GLOWING_FILL_COLOR)
            painter.setBrush(fill)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRoundedRect(
                start.x(),
                start.y(),
                Block.side,
                Block.side * (1 + self.trail),
                20,
                20,
                QtCore.Qt.RelativeSize,
            )

        if self.glowing:
            fill = QtGui.QRadialGradient(self.center, self.glowing * Block.side)
            fill.setColorAt(0, self.TRANSPARENT)
            fill.setColorAt(0.5 / self.glowing, self.LIGHT_COLOR)
            fill.setColorAt(1, self.TRANSPARENT)
            painter.setBrush(QtGui.QBrush(fill))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(
                self.center.x() - self.glowing * Block.side,
                self.center.y() - self.glowing * Block.side,
                2 * self.glowing * Block.side,
                2 * self.glowing * Block.side,
            )

        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(
            p.x() + 1,
            p.y() + 1,
            Block.side - 2,
            Block.side - 2,
            20,
            20,
            QtCore.Qt.RelativeSize,
        )

    def brush(self):
        if self.fill_color is None:
            return QtCore.Qt.NoBrush

        fill = QtGui.QRadialGradient(self.glint, 1.5 * Block.side)
        fill.setColorAt(0, self.fill_color.lighter())
        fill.setColorAt(1, self.fill_color)
        return QtGui.QBrush(fill)

    def pen(self):
        if self.border_color is None:
            return QtCore.Qt.NoPen

        border = QtGui.QRadialGradient(self.glint, Block.side)
        border.setColorAt(0, self.border_color.lighter())
        border.setColorAt(1, self.border_color.darker())
        return QtGui.QPen(QtGui.QBrush(border), 1, join=QtCore.Qt.RoundJoin)

    def shine(self, glowing=2, delay=None):
        self.border_color = Block.GLOWING_BORDER_COLOR
        self.fill_color = Block.GLOWING_FILL_COLOR
        self.glowing = glowing
        if delay:
            QtCore.QTimer.singleShot(delay, self.fade)

    def fade(self):
        self.border_color = Block.BORDER_COLOR
        self.fill_color = Block.FILL_COLOR
        self.glowing = 0
        self.trail = 0


class GhostBlock(Block):
    """
    Mino of the ghost piece
    """

    BORDER_COLOR = consts.GHOST_BLOCK_BORDER_COLOR 
    FILL_COLOR = consts.GHOST_BLOCK_FILL_COLOR
    GLOWING_FILL_COLOR = consts.GHOST_BLOCK_GLOWING_FILL_COLOR
    GLOWING = consts.GHOST_BLOCK_GLOWING 