#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import consts
from qt5 import QtWidgets, QtGui
from block import Block
from point import Point
from settings import s, settings
from tetromino import Tetromino


class Grid(QtWidgets.QWidget):
    """
    Mother class of Hold queue, Matrix, Next piece, and Next queue
    """

    ROWS = consts.GRID_DEFAULT_ROWS + consts.GRID_INVISIBLE_ROWS
    COLUMNS = consts.GRID_DEFAULT_COLUMNS
    STARTING_POSITION = Point(
        consts.GRID_DEFAULT_COLUMNS // 2,
        consts.GRID_DEFAULT_ROWS // 2 + 2
    )
    GRIDLINE_COLOR = consts.GRID_GRIDLINE_COLOR 
    HARD_DROP_MOVEMENT = consts.GRID_HARD_DROP_MOVEMENT
    SPOTLIGHT = Point(*consts.GRID_SPOTLIGHT )

    def __init__(self, frames):
        super().__init__(frames)
        self.setStyleSheet("background-color: transparent")
        self.frames = frames
        self.spotlight = self.SPOTLIGHT
        self.piece = None

    def insert(self, piece, position=None):
        """
        Add a Tetromino to self
        Update its coordinates
        """
        piece.insert_into(self, position or self.STARTING_POSITION)
        self.piece = piece
        self.update()

    def resizeEvent(self, event):
        self.bottom = Block.side * self.ROWS
        self.grid_top = consts.GRID_INVISIBLE_ROWS * Block.side
        width = Block.side * self.COLUMNS
        self.left = (self.width() - width) // 2
        self.right = width + self.left
        self.top_left_corner = Point(self.left, 0)

    def paintEvent(self, event=None):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        self.paint_grid(painter)

        if (not self.frames.paused or not self.frames.playing) and self.piece:
            self.paint_piece(painter, self.piece)

    def paint_grid(self, painter):
        painter.setPen(self.GRIDLINE_COLOR)
        for x in (self.left + i * Block.side for i in range(self.COLUMNS + 1)):
            painter.drawLine(x, self.grid_top, x, self.bottom)
        for y in (j * Block.side for j in range(consts.GRID_INVISIBLE_ROWS, self.ROWS + 1)):
            painter.drawLine(self.left, y, self.right, y)

    def paint_piece(self, painter, piece):
        for mino in piece.minoes:
            mino.paint(painter, self.top_left_corner, self.spotlight)


class HoldQueue(Grid):
    """
    The Hold Queue allows the player to “hold” a falling Tetrimino for as long as they wish.
    Holding a Tetrimino releases the Tetrimino already in the Hold Queue (if one exists).
    """

    def paintEvent(self, event):
        if not settings[s.OTHER][s.HOLD_ENABLED]:
            return

        super().paintEvent(event)


class NextQueue(Grid):
    """
    The Next Queue allows the player to see the Next Tetrimino that will be generated
    and put into play.
    """

    ROWS = consts.NEXT_QUEUE_ROWS
    COLUMNS = consts.NEXT_QUEUE_COLUMNS

    def __init__(self, parent):
        super().__init__(parent)
        self.pieces = []

    def new_piece(self):
        self.pieces = self.pieces[1:] + [Tetromino()]
        self.insert_pieces()

    def insert_pieces(self):
        for y, piece in enumerate(self.pieces):
            piece.insert_into(self, Point(3, 3 * y + 1))

    def paintEvent(self, event=None):
        if not settings[s.OTHER][s.SHOW_NEXT_QUEUE]:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if not self.frames.paused:
            for piece in self.pieces:
                self.paint_piece(painter, piece)