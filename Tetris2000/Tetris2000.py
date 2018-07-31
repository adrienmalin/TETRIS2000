#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Another TETRIS® clone
Tetris Game Design by Alexey Pajitnov.
Parts of comments issued from 2009 Tetris Design Guideline
"""

__author__ = "Adrien Malingrey"
__title__ = "Tetris 2000"
__version__ = "0.2"


import sys
import os
import random
import locale
import time
import itertools
import ctypes
import collections

try:  # PyQt5
    from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia
except ImportError:
    try:  # PySide2
        from PySide2 import QtWidgets, QtCore, QtGui, QtMultimedia
    except ImportError:
        sys.exit(
            "This program require a Qt library.\n"
            "You can install PyQt5 package (recommended) :\n"
            "    pip install PyQt5\n"
            "or PySide2 package :\n"
            "    pip install PySide2\n"
            "NB : On Windows, PySide2 may require to install\n"
            "Visual C++ Redistributable Packages separately."
        )
    else:
        os.environ["QT_API"] = "pyside2"
else:
    os.environ["QT_API"] = "pyqt5"
    QtCore.Signal = QtCore.pyqtSignal


# Consts
# Paths
PATH = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(PATH, "data", "icons", "icon.ico")
BG_IMAGE_DIR = os.path.join(PATH, "data", "backgrounds")
MUSIC_PATH = os.path.join(PATH, "data", "sounds", "Tetris - Song A.mp3")
SOUNDS_DIR = os.path.join(PATH, "data", "sounds")
LOCALE_PATH = os.path.join(PATH, "data", "locale")
FONTS_DIR = os.path.join(PATH, "data", "fonts")
# Coordinates and direction
L, R, U, D = -1, 1, -1, 1  # Left, Right, Up, Down
CLOCKWISE, COUNTERCLOCKWISE = 1, -1
# Delay
ANIMATION_DELAY = 100  # milliseconds


class Point(QtCore.QPoint):
    """
    Point of coordinates (x, y)
    """

    def __init__(self, x, y):
        super().__init__(x, y)

    def __add__(self, o):
        return Point(self.x() + o.x(), self.y() + o.y())

    def __sub__(self, o):
        return Point(self.x() - o.x(), self.y() - o.y())

    def __mul__(self, k):
        return Point(k * self.x(), k * self.y())

    def __truediv__(self, k):
        return Point(self.x() / k, k * self.y() / k)

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__

    def rotate(self, center, direction=CLOCKWISE):
        """ Returns the Point image of the rotation of self
        through 90° CLOKWISE or COUNTERCLOCKWISE around center"""
        if self == center:
            return self

        p = self - center
        p = Point(-direction * p.y(), direction * p.x())
        p += center
        return p


class Block:
    """
    Mino or block
    Mino : A single square-shaped building block of a shape called a Tetrimino.
    Four Minos arranged into any of their various connected patterns is known as a Tetrimino
    Block : A single block locked in a cell in the Grid
    """

    # Colors
    BORDER_COLOR = QtGui.QColor(0, 159, 218, 255)
    FILL_COLOR = QtGui.QColor(0, 159, 218, 25)
    GLOWING_BORDER_COLOR = None
    GLOWING_FILL_COLOR = QtGui.QColor(186, 211, 255, 70)
    LIGHT_COLOR = QtGui.QColor(204, 255, 255, 40)
    TRANSPARENT = QtGui.QColor(255, 255, 255, 0)
    GLOWING = 0

    side = 0

    def __init__(self, coord, trail=0):
        self.coord = coord
        self.trail = trail
        self.border_color = self.BORDER_COLOR
        self.fill_color = self.FILL_COLOR
        self.glowing = self.GLOWING

    def paint(self, painter, top_left_corner, spotlight):
        p = top_left_corner + self.coord * Block.side
        self.center = p + QtCore.QPoint(Block.side / 2, Block.side / 2)
        self.glint = 0.15 * Block.side * spotlight + 0.85 * self.center

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

    BORDER_COLOR = QtGui.QColor(135, 213, 255, 255)
    FILL_COLOR = None
    GLOWING_FILL_COLOR = QtGui.QColor(201, 149, 205, 255)
    GLOWING = 1


class MetaTetro(type):
    """
    Save the different shapes of Tetrominoes
    """

    def __init__(cls, name, bases, dico):
        type.__init__(cls, name, bases, dico)
        Tetromino.classes.append(cls)
        Tetromino.nb_classes += 1


class Tetromino:
    """
    Geometric Tetris® shape formed by four Minos connected along their sides.
    A total of seven possible Tetriminos can be made using four Minos.
    """

    COORDS = NotImplemented
    SUPER_ROTATION_SYSTEM = (
        {
            COUNTERCLOCKWISE: ((0, 0), (R, 0), (R, U), (0, 2 * D), (R, 2 * D)),
            CLOCKWISE: ((0, 0), (L, 0), (L, U), (0, 2 * D), (L, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((0, 0), (R, 0), (R, D), (0, 2 * U), (R, 2 * U)),
            CLOCKWISE: ((0, 0), (R, 0), (R, D), (0, 2 * U), (R, 2 * U)),
        },
        {
            COUNTERCLOCKWISE: ((0, 0), (L, 0), (L, U), (0, 2 * D), (L, 2 * D)),
            CLOCKWISE: ((0, 0), (R, 0), (R, U), (0, 2 * D), (R, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((0, 0), (L, 0), (L, D), (0, 2 * U), (L, 2 * U)),
            CLOCKWISE: ((0, 0), (L, 0), (L, D), (0, 2 * D), (L, 2 * U)),
        },
    )

    classes = []
    nb_classes = 0
    random_bag = []

    def __new__(cls):
        """
        Return a Tetromino using the 7-bag Random Generator
        Tetris uses a “bag” system to determine the sequence of Tetriminos
        that appear during game play.
        This system allows for equal distribution among the seven Tetriminos.
        The seven different Tetriminos are placed into a virtual bag,
        then shuffled into a random order.
        This order is the sequence that the bag “feeds” the Next Queue.
        Every time a new Tetrimino is generated and starts its fall within the Matrix,
        the Tetrimino at the front of the line in the bag is placed at the end of the Next Queue,
        pushing all Tetriminos in the Next Queue forward by one.
        The bag is refilled and reshuffled once it is empty.
        """
        if not cls.random_bag:
            cls.random_bag = random.sample(cls.classes, cls.nb_classes)
        return super().__new__(cls.random_bag.pop())

    def __init__(self):
        self.orientation = 0
        self.t_spin = ""

    def insert_into(self, matrix, position):
        self.matrix = matrix
        self.minoes = tuple(Block(Point(*coord) + position) for coord in self.COORDS)

    def _try_movement(self, next_coords_generator, trail=False):
        """
        Test if self can fit in the Grid with new coordinates,
        i.e. all cells are empty.
        If it can, change self's coordinates and return True.
        Else, make no changes and return False
        Update the Grid if there is no drop trail
        """
        futures_coords = []
        for p in next_coords_generator:
            if not self.matrix.is_empty_cell(p):
                return False
            futures_coords.append(p)

        for block, future_coord in zip(self.minoes, futures_coords):
            block.coord = future_coord
        if not trail:
            self.matrix.update()
        return True

    def move(self, horizontally, vertically, trail=False):
        """
        Try to translate self horizontally or vertically
        The Tetrimino in play falls from just above the Skyline one cell at a time,
        and moves left and right one cell at a time.
        Each Mino of a Tetrimino “snaps” to the appropriate cell position at the completion of a move,
        although intermediate Tetrimino movement appears smooth.
        Only right, left, and downward movement are allowed.
        Movement into occupied cells and Matrix walls and floors is not allowed
        Update the Grid if there is no drop trail
        """
        return self._try_movement(
            (block.coord + Point(horizontally, vertically) for block in self.minoes),
            trail,
        )

    def rotate(self, direction=CLOCKWISE):
        """
        Try to rotate self through 90° CLOCKWISE or COUNTERCLOCKWISE around its center
        Tetriminos can rotate clockwise and counterclockwise using the Super Rotation System.
        This system allows Tetrimino rotation in situations that
        the original Classic Rotation System did not allow,
        such as rotating against walls.
        Each time a rotation button is pressed,
        the Tetrimino in play rotates 90 degrees in the clockwise or counterclockwise direction.
        Rotation can be performed while the Tetrimino is Auto-Repeating left or right.
        There is no Auto-Repeat for rotation itself.
        """
        rotated_coords = tuple(
            block.coord.rotate(self.minoes[0].coord, direction) for block in self.minoes
        )

        for movement in self.SUPER_ROTATION_SYSTEM[self.orientation][direction]:
            if self._try_movement(coord + Point(*movement) for coord in rotated_coords):
                self.orientation = (self.orientation + direction) % 4
                return True
        return False

    def soft_drop(self):
        """
        Causes the Tetrimino to drop at an accelerated rate (s.AUTO_REPEAT_RATE)
        from its current location
        """
        dropped = self.move(0, D, trail=True)
        if dropped:
            for block in self.minoes:
                block.trail = 1
            self.matrix.update()
        return dropped

    def hard_drop(self):
        """
        Causes the Tetrimino in play to drop straight down instantly from its
        current location and Lock Down on the first Surface it lands on.
        It does not allow for further player manipulation of the Tetrimino in play.
        """
        trail = 0
        while self.move(0, D, trail=True):
            trail += 1
        for block in self.minoes:
            block.trail = trail
        self.matrix.update()
        return trail


class TetroI(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital I
    four minoes in a straight line
    """

    COORDS = (L, 0), (2 * L, 0), (0, 0), (R, 0)
    SUPER_ROTATION_SYSTEM = (
        {
            COUNTERCLOCKWISE: ((0, D), (L, D), (2 * R, D), (L, U), (2 * R, 2 * D)),
            CLOCKWISE: ((R, 0), (L, 0), (2 * R, 0), (L, D), (2 * R, 2 * U)),
        },
        {
            COUNTERCLOCKWISE: ((L, 0), (R, 0), (2 * L, 0), (R, U), (2 * L, 2 * D)),
            CLOCKWISE: ((0, D), (L, D), (2 * R, D), (L, U), (2 * R, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((0, U), (R, U), (2 * L, U), (R, D), (2 * L, 2 * U)),
            CLOCKWISE: ((L, 0), (R, 0), (2 * L, 0), (R, U), (2 * L, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((R, 0), (L, 0), (2 * R, 0), (L, D), (2 * R, 2 * U)),
            CLOCKWISE: ((0, U), (R, U), (2 * L, U), (R, D), (2 * L, 2 * U)),
        },
    )


class TetroT(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital T
    a row of three minoes with one added above the center
    Can perform a T-Spin
    """

    COORDS = (0, 0), (L, 0), (0, U), (R, 0)
    T_SLOT_A = ((L, U), (R, U), (R, D), (L, D))
    T_SLOT_B = ((R, U), (R, D), (L, D), (L, U))
    T_SLOT_C = ((L, D), (L, U), (R, U), (R, D))
    T_SLOT_D = ((R, D), (L, D), (L, U), (R, U))

    def __init__(self):
        super().__init__()

    def rotate(self, direction=CLOCKWISE):
        """
        Detects T-Spins:
        this action can be achieved by first landing a T-Tetrimino,
        and before it Locks Down, rotating it in a T-Slot
        (any Block formation such that when the T-Tetrimino is spun into it,
        any three of the four cells diagonally adjacent to the center of self
        are occupied by existing Blocks.)
        """
        rotated = super().rotate(direction)
        if rotated:
            center = self.minoes[0].coord
            pa = center + Point(*self.T_SLOT_A[self.orientation])
            pb = center + Point(*self.T_SLOT_B[self.orientation])
            pc = center + Point(*self.T_SLOT_C[self.orientation])
            pd = center + Point(*self.T_SLOT_D[self.orientation])

            a = not self.matrix.is_empty_cell(pa)
            b = not self.matrix.is_empty_cell(pb)
            c = not self.matrix.is_empty_cell(pc)
            d = not self.matrix.is_empty_cell(pd)

            if (a and b) and (c or d):
                if c:
                    pe = (pa + pc) / 2
                elif d:
                    pe = (pb + pd) / 2
                if not self.matrix.is_empty_cell(pe):
                    self.t_spin = "T-Spin"
            elif (a or b) and (c and d):
                self.t_spin = "Mini T-Spin"
        return rotated


class TetroZ(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital Z
    two stacked horizontal dominoes with the top one offset to the left
    """

    COORDS = (0, 0), (L, U), (0, U), (R, 0)


class TetroS(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital S
    two stacked horizontal dominoes with the top one offset to the right
    """

    COORDS = (0, 0), (0, U), (L, 0), (R, U)


class TetroL(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital L
    a row of three minoes with one added above the right side
    """

    COORDS = (0, 0), (L, 0), (R, 0), (R, U)


class TetroJ(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital J
    a row of three minoes with one added above the left side
    """

    COORDS = (0, 0), (L, U), (L, 0), (R, 0)


class TetroO(Tetromino, metaclass=MetaTetro):
    """
    Square shape
    four minoes in a 2×2 square.
    """

    COORDS = (0, 0), (L, 0), (0, U), (L, U)

    def rotate(self, direction=1):
        """ irrelevant """
        pass


class Ghost(Tetromino):
    """
    A graphical representation of where the Tetrimino in play will come to rest
    if it is dropped from its current position.
    """

    def __new__(cls, piece):
        return object.__new__(cls)

    def __init__(self, piece):
        self.matrix = piece.matrix
        self.minoes = tuple(
            GhostBlock(Point(mino.coord.x(), mino.coord.y())) for mino in piece.minoes
        )
        self.hard_drop()

    def hard_drop(self):
        while self.move(0, D):
            pass


class Grid(QtWidgets.QWidget):
    """
    Mother class of Hold queue, Next piece Queue, Matrix, and Next queue
    """

    ROWS = 6
    COLUMNS = 6
    STARTING_POSITION = Point(3, 4)
    GRIDLINE_COLOR = QtGui.QColor(255, 255, 255, 60)
    HARD_DROP_MOVEMENT = 0.2
    SPOTLIGHT = Point(0, 0)

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
        self.grid_top = 2 * Block.side
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
        for y in (j * Block.side for j in range(2, self.ROWS + 1)):
            painter.drawLine(self.left, y, self.right, y)

    def paint_piece(self, painter, piece):
        for mino in piece.minoes:
            mino.paint(painter, self.top_left_corner, self.spotlight)


class Matrix(Grid):
    """
    The rectangular arrangement of cells creating the active game area.
    Tetriminos fall from the top-middle just above the Skyline (off-screen) to the bottom.
    """

    ROWS = 22
    COLUMNS = 10
    STARTING_POSITION = Point(COLUMNS // 2, 1)
    TEXT_COLOR = QtGui.QColor(204, 255, 255, 128)
    TEMPORARY_TEXT_DURATION = 1000  # milliseconds

    #  Delays
    INITIAL_SPEED = 1000  # row per milliseconds
    ENTRY_DELAY = 80  # millisecondes
    LINE_CLEAR_DELAY = 80  # millisecondes
    LOCK_DELAY = 500  # millisecondes

    drop_signal = QtCore.Signal(int)
    lock_signal = QtCore.Signal(int, str)

    def __init__(self, frames):
        super().__init__(frames)

        self.game_over = False
        self.text = ""
        self.temporary_texts = []

        self.load_sounds()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.auto_repeat_delay = 0
        self.auto_repeat_timer = QtCore.QTimer()
        self.auto_repeat_timer.timeout.connect(self.auto_repeat)
        self.fall_timer = QtCore.QTimer()
        self.fall_timer.timeout.connect(self.fall)

        self.cells = []
        self.apply_settings()

    def load_sounds(self):
        self.hard_drop_sound = QtMultimedia.QSoundEffect(self)
        self.hard_drop_sound.setSource(
            QtCore.QUrl.fromLocalFile(
                os.path.join(SOUNDS_DIR, "hard_drop.wav")
            )
        )
        self.rotate_sound = QtMultimedia.QSoundEffect(self)
        self.rotate_sound.setSource(
            QtCore.QUrl.fromLocalFile(
                os.path.join(SOUNDS_DIR,"rotate.wav")
            )
        )

    def apply_settings(self):
        self.keys = {
            getattr(QtCore.Qt, "Key_" + name): action
            for action, name in settings[s.KEYBOARD].items()
        }
        self.auto_repeat_timer.start(settings[s.DELAYS][s.AUTO_REPEAT_RATE])
        self.spotlight = self.SPOTLIGHT
        for sound in self.hard_drop_sound, self.rotate_sound:
            sound.setVolume(settings[s.SOUND][s.EFFECTS_VOLUME])

    def new_game(self):
        self.game_over = False
        self.lock_delay = self.LOCK_DELAY
        self.cells = [self.empty_row() for y in range(self.ROWS)]
        self.setFocus()
        self.actions_to_repeat = []

    def new_level(self, level):
        self.show_temporary_text(self.tr("Level\n") + str(level))
        self.speed = self.INITIAL_SPEED * (0.8 - ((level - 1) * 0.007)) ** (level - 1)
        self.fall_timer.start(self.speed)
        if level > 15:
            self.lock_delay *= 0.9

    def empty_row(self):
        return [None for x in range(self.COLUMNS)]

    def is_empty_cell(self, coord):
        x, y = coord.x(), coord.y()
        return 0 <= x < self.COLUMNS and y < self.ROWS and not self.cells[y][x]

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        if not self.frames.playing:
            return

        try:
            action = self.keys[event.key()]
        except KeyError:
            return

        self.do(action)
        if action in (s.MOVE_LEFT, s.MOVE_RIGHT, s.SOFT_DROP):
            if action not in self.actions_to_repeat:
                self.actions_to_repeat.append(action)
                self.auto_repeat_wait()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return

        if not self.frames.playing:
            return

        try:
            self.actions_to_repeat.remove(self.keys[event.key()])
        except (KeyError, ValueError):
            pass
        else:
            self.auto_repeat_wait()

        if not self.actions_to_repeat:
            for mino in self.piece.minoes:
                mino.fade()
            self.update()

    def auto_repeat_wait(self):
        self.auto_repeat_delay = (
            time.time() + settings[s.DELAYS][s.AUTO_SHIFT_DELAY] / 1000
        )

    def auto_repeat(self):
        """
        Tapping the move button allows a single cell movement of the Tetrimino
        in the direction pressed.
        Holding down the move button triggers an Auto-Repeat movement
        that allows the player to move a Tetrimino from one side of the Matrix
        to the other in about 0.5 seconds.
        This is essential on higher levels when the Fall Speed of a Tetrimino is very fast.
        There is a slight delay between the time the move button is pressed
        and the time when Auto-Repeat kicks in : s.AUTO_SHIFT_DELAY.
        This delay prevents unwanted extra movement of a Tetrimino.
        Auto-Repeat only affects Left/Right movement.
        Auto-Repeat continues to the Next Tetrimino (after Lock Down)
        as long as the move button remains pressed.
        In addition, when Auto-Repeat begins,
        and the player then holds the opposite direction button,
        the Tetrimino then begins moving the opposite direction with the initial delay.
        When any single button is then released,
        the Tetrimino should again move in the direction still held,
        with the Auto-Shift delay applied once more.
        """
        if (
            not self.frames.playing
            or self.frames.paused
            or time.time() < self.auto_repeat_delay
        ):
            return

        if self.actions_to_repeat:
            self.do(self.actions_to_repeat[-1])

    def do(self, action):
        """The player can move, rotate, Soft Drop, Hard Drop,
        and Hold the falling Tetrimino (i.e., the Tetrimino in play).
        """
        if action == s.PAUSE:
            self.frames.pause(not self.frames.paused)

        if not self.frames.playing or self.frames.paused or not self.piece:
            return

        for mino in self.piece.minoes:
            mino.shine(0)

        if action == s.MOVE_LEFT:
            if self.piece.move(L, 0):
                self.lock_wait()

        elif action == s.MOVE_RIGHT:
            if self.piece.move(R, 0):
                self.lock_wait()

        elif action == s.ROTATE_CLOCKWISE:
            if self.piece.rotate(direction=CLOCKWISE):
                self.rotate_sound.play()
                self.lock_wait()

        elif action == s.ROTATE_COUNTERCLOCKWISE:
            if self.piece.rotate(direction=COUNTERCLOCKWISE):
                self.rotate_sound.play()
                self.lock_wait()

        elif action == s.SOFT_DROP:
            if self.piece.soft_drop():
                self.drop_signal.emit(1)

        elif action == s.HARD_DROP:
            trail = self.piece.hard_drop()
            self.hard_drop_sound.play()
            self.top_left_corner += Point(0, self.HARD_DROP_MOVEMENT * Block.side)
            self.drop_signal.emit(2 * trail)
            QtCore.QTimer.singleShot(ANIMATION_DELAY, self.after_hard_drop)
            self.lock_phase()

        elif action == s.HOLD:
            self.frames.hold()

    def after_hard_drop(self):
        """ Reset the animation movement of the Matrix on a hard drop """
        self.top_left_corner -= Point(0, self.HARD_DROP_MOVEMENT * Block.side)

    def lock_wait(self):
        self.fall_delay = time.time() + (self.speed + self.lock_delay) / 1000

    def fall(self):
        """
        Once a Tetrimino is generated,
        it immediately drops one row (if no existing Block is in its path).
        From here, it begins its descent to the bottom of the Matrix.
        The Tetrimino will fall at its normal Fall Speed
        whether or not it is being manipulated by the player.
        """
        if self.piece:
            if self.piece.move(0, 1):
                self.lock_wait()
            else:
                if time.time() >= self.fall_delay:
                    self.lock_phase()

    def lock_phase(self):
        """
        The player can perform the same actions on a Tetrimino in this phase
        as he/she can in the Falling Phase,
        as long as the Tetrimino is not yet Locked Down.
        A Tetrimino that is Hard Dropped Locks Down immediately.
        However, if a Tetrimino naturally falls or Soft Drops onto a landing Surface,
        it is given a delay (self.fall_delay) on a Lock Down Timer
        before it actually Locks Down.
        """
        #  Enter minoes into the matrix
        for mino in self.piece.minoes:
            if mino.coord.y() >= 0:
                self.cells[mino.coord.y()][mino.coord.x()] = mino
            mino.shine(glowing=2, delay=ANIMATION_DELAY)
        self.update()

        if all(mino.coord.y() <= 1 for mino in self.piece.minoes):
            self.frames.game_over()
            return

        """
        In this phase,
        the engine looks for patterns made from Locked Down Blocks in the Matrix.
        Once a pattern has been matched,
        it can trigger any number of Tetris variant-related effects.
        The classic pattern is the Line Clear pattern.
        This pattern is matched when one or more rows of 10 horizontally aligned
        Matrix cells are occupied by Blocks.
        The matching Blocks are then marked for removal on a hit list.
        Blocks on the hit list are cleared from the Matrix at a later time
        in the Eliminate Phase.
        """
        # Dectect complete lines
        self.complete_lines = []
        for y, row in enumerate(self.cells):
            if all(cell for cell in row):
                self.complete_lines.append(y)
                for block in row:
                    block.shine()
                self.spotlight = row[self.COLUMNS // 2].coord
                self.auto_repeat_timer.stop()
        self.lock_signal.emit(len(self.complete_lines), self.piece.t_spin)

        if not self.complete_lines:
            self.frames.new_piece()
            return

        self.fall_timer.stop()
        QtCore.QTimer.singleShot(self.LINE_CLEAR_DELAY, self.eliminate_phase)

    def eliminate_phase(self):
        """
        Any Minos marked for removal, i.e., on the hit list,
        are cleared from the Matrix in this phase.
        If this results in one or more complete 10-cell rows in the Matrix
        becoming unoccupied by Minos,
        then all Minos above that row(s) collapse,
        or fall by the number of complete rows cleared from the Matrix.
        """
        for y in self.complete_lines:
            del self.cells[y]
            self.cells.insert(0, self.empty_row())

        for y, row in enumerate(self.cells):
            for x, block in enumerate(row):
                if block:
                    block.coord.setX(x)
                    block.coord.setY(y)

        self.update()
        self.auto_repeat_wait()
        self.auto_repeat_timer.start(settings[s.DELAYS][s.AUTO_REPEAT_RATE])

        self.frames.new_piece()

    def paintEvent(self, event):
        """
        Draws grid, actual piece, blocks in the Matrix and show texts
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        self.paint_grid(painter)

        if not self.frames.paused or self.game_over:
            if self.piece:
                if settings[s.OTHER][s.GHOST]:
                    self.ghost = Ghost(self.piece)
                    self.spotlight = self.ghost.minoes[0].coord
                    self.paint_piece(painter, self.ghost)
                self.paint_piece(painter, self.piece)

            # Blocks in matrix
            for row in self.cells:
                for block in row:
                    if block:
                        block.paint(painter, self.top_left_corner, self.spotlight)

        if self.frames.playing and self.frames.paused:
            painter.setFont(QtGui.QFont("Maassslicer", 0.75 * Block.side))
            painter.setPen(self.TEXT_COLOR)
            painter.drawText(
                self.rect(),
                QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap,
                self.tr("PAUSE\n\nPress %s\nto resume") % settings[s.KEYBOARD][s.PAUSE],
            )
        if self.game_over:
            painter.setFont(QtGui.QFont("Maassslicer", Block.side))
            painter.setPen(self.TEXT_COLOR)
            painter.drawText(
                self.rect(),
                QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap,
                self.tr("GAME\nOVER"),
            )
        if self.temporary_texts:
            painter.setFont(self.temporary_text_font)
            painter.setPen(self.TEXT_COLOR)
            painter.drawText(
                self.rect(),
                QtCore.Qt.AlignHCenter | QtCore.Qt.TextWordWrap,
                "\n\n".join(self.temporary_texts),
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.temporary_text_font = QtGui.QFont("Maassslicer", Block.side)

    def show_temporary_text(self, text):
        self.temporary_texts.append(text.upper())
        self.font = self.temporary_text_font
        self.update()
        QtCore.QTimer.singleShot(self.TEMPORARY_TEXT_DURATION, self.delete_text)

    def delete_text(self):
        del self.temporary_texts[0]
        self.update()

    def focusOutEvent(self, event):
        if self.frames.playing:
            self.frames.pause(True)


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

    ROWS = 16
    COLUMNS = 6

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


class Stats(QtWidgets.QWidget):
    """
    Show informations relevant to the game being played is displayed on-screen.
    Looks for patterns made from Locked Down Blocks in the Matrix and calculate score.
    """

    ROWS = 15
    COLUMNS = 6
    TEXT_COLOR = QtGui.QColor(0, 159, 218, 128)

    temporary_text = QtCore.Signal(str)

    def __init__(self, frames):
        super().__init__(frames)
        self.frames = frames
        self.setStyleSheet("background-color: transparent")

        self.SCORES = (
            {"name": "", "": 0, "Mini T-Spin": 1, "T-Spin": 4},
            {"name": self.tr("Single"), "": 1, "Mini T-Spin": 2, "T-Spin": 8},
            {"name": self.tr("Double"), "": 3, "T-Spin": 12},
            {"name": self.tr("Triple"), "": 5, "T-Spin": 16},
            {"name": self.tr("Tetris"), "": 8},
        )

        self.load_sounds()

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.text_options = QtGui.QTextOption(QtCore.Qt.AlignRight)
        self.text_options.setWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)

        self.clock = QtCore.QTimer()
        self.clock.timeout.connect(self.tick)

        self.high_score = int(qsettings.value(self.tr("High score"), 0))

    def load_sounds(self):
        self.line_clear_sound = QtMultimedia.QSoundEffect(self)
        self.line_clear_sound.setSource(
            QtCore.QUrl.fromLocalFile(
                os.path.join(SOUNDS_DIR, "line_clear.wav")
            )
        )
        self.tetris_sound = QtMultimedia.QSoundEffect(self)
        self.tetris_sound.setSource(
            QtCore.QUrl.fromLocalFile(
                os.path.join(SOUNDS_DIR, "tetris.wav")
            )
        )
        for sound in self.line_clear_sound, self.tetris_sound:
            sound.setVolume(settings[s.SOUND][s.EFFECTS_VOLUME])

    def new_game(self):
        self.level -= 1
        self.goal = 0
        self.complete_lines_total = 0
        self.score_total = 1
        self.t_spin_total = 0
        self.mini_t_spin_total = 0
        self.nb_back_to_back = 0
        self.back_to_back_scores = None
        self.combo = -1
        self.combos_total = 0
        self.max_combo = 0
        self.chronometer = 0
        self.nb_tetro = 0
        self.clock.start(1000)
        self.lines_stats = [0, 0, 0, 0, 0]

    def new_level(self):
        self.level += 1
        self.goal += 5 * self.level
        return self.level

    def update_score(self, nb_complete_lines, t_spin):
        """
        The player scores points by performing Single, Double, Triple,
        and Tetris Line Clears, as well as T-Spins and Mini T-Spins.
        Soft and Hard Drops also award points.
        There is a special bonus for Back-to-Backs,
        which is when two actions such as a Tetris and T-Spin Double take place
        without a Single, Double, or Triple Line Clear occurring between them.
        Scoring for Line Clears, T-Spins, and Mini T-Spins are level dependent,
        while Hard and Soft Drop point values remain constant.
        """
        self.nb_tetro += 1
        if nb_complete_lines:
            self.complete_lines_total += nb_complete_lines
            self.lines_stats[nb_complete_lines] += 1
        if t_spin == "T-Spin":
            self.t_spin_total += 1
        elif t_spin == "Mini T-Spin":
            self.mini_t_spin_total += 1

        score = self.SCORES[nb_complete_lines][t_spin]

        if score:
            text = " ".join((t_spin, self.SCORES[nb_complete_lines]["name"]))
            if (t_spin and nb_complete_lines) or nb_complete_lines == 4:
                self.tetris_sound.play()
            if 1 <= nb_complete_lines <= 3:
                self.line_clear_sound.play()

            self.goal -= score
            score = 100 * self.level * score
            self.score_total += score

            self.temporary_text.emit(text + "\n{:n}".format(score))
                
# ==============================================================================
#         Combo
#         Bonus for complete lines on each consecutive lock downs
#         if nb_complete_lines:
# ==============================================================================
        if nb_complete_lines:
            self.combo += 1
            if self.combo > 0:
                if nb_complete_lines == 1:
                    combo_score = 20 * self.combo * self.level
                else:
                    combo_score = 50 * self.combo * self.level
                self.score_total += combo_score
                self.max_combo = max(self.max_combo, self.combo)
                self.combos_total += 1
                self.temporary_text.emit(
                    self.tr("COMBO x{:n}\n{:n}").format(self.combo, combo_score)
                )
        else:
            self.combo = -1

# ==============================================================================
#         Back-to_back sequence
#         Two major bonus actions, such as two Tetrises, performed without
#         a Single, Double, or Triple Line Clear occurring between them.
#         Bonus for Tetrises, T-Spin Line Clears, and Mini T-Spin Line Clears
#         performed consecutively in a B2B sequence.
# ==============================================================================
        if (t_spin and nb_complete_lines) or nb_complete_lines == 4:
            if self.back_to_back_scores is not None:
                self.back_to_back_scores.append(score // 2)
            else:
                # The first Line Clear in the Back-to-Back sequence
                # does not receive the Back-to-Back Bonus.
                self.back_to_back_scores = []
        elif nb_complete_lines and not t_spin:
            # A Back-to-Back sequence is only broken by a Single, Double, or Triple Line Clear.
            # Locking down a Tetrimino without clearing a line
            # or holding a Tetrimino does not break the Back-to-Back sequence.
            # T-Spins and Mini T-Spins that do not clear any lines
            # do not receive the Back-to-Back Bonus; instead they are scored as normal.
            # They also cannot start a Back-to-Back sequence, however,
            # they do not break an existing Back-to-Back sequence.
            if self.back_to_back_scores:
                b2b_score = sum(self.back_to_back_scores)
                self.score_total += b2b_score
                self.nb_back_to_back += 1
                self.temporary_text.emit(
                    self.tr("BACK TO BACK\n{:n}").format(b2b_score)
                )
            self.back_to_back_scores = None

        self.high_score = max(self.score_total, self.high_score)
        self.update()

    def update_drop_score(self, n):
        """ Tetrimino is Soft Dropped for n lines or Hard Dropped for (n/2) lines"""
        self.score_total += n
        self.high_score = max(self.score_total, self.high_score)
        self.update()

    def tick(self):
        self.chronometer += 1
        self.update()

    def paintEvent(self, event):
        if not self.frames.playing and not self.frames.board.game_over:
            return

        painter = QtGui.QPainter(self)
        painter.setFont(self.font)
        painter.setPen(self.TEXT_COLOR)

        painter.drawText(
            QtCore.QRectF(self.rect()), self.text(sep="\n\n"), self.text_options
        )

    def text(self, full_stats=False, sep="\n"):
        text = (
            self.tr("Score: ")
            + locale.format("%i", self.score_total, grouping=True, monetary=True)
            + sep
            + self.tr("High score: ")
            + locale.format("%i", self.high_score, grouping=True, monetary=True)
            + sep
            + self.tr("Time: {}\n").format(
                time.strftime("%H:%M:%S", time.gmtime(self.chronometer))
            )
            + sep
            + self.tr("Level: ")
            + locale.format("%i", self.level, grouping=True, monetary=True)
            + sep
            + self.tr("Goal: ")
            + locale.format("%i", self.goal, grouping=True, monetary=True)
            + sep
            + self.tr("Lines: ")
            + locale.format(
                "%i", self.complete_lines_total, grouping=True, monetary=True
            )
            + sep
            + self.tr("Mini T-Spins: ")
            + locale.format("%i", self.mini_t_spin_total, grouping=True, monetary=True)
            + sep
            + self.tr("T-Spins: ")
            + locale.format("%i", self.t_spin_total, grouping=True, monetary=True)
            + sep
            + self.tr("Back-to-back: ")
            + locale.format("%i", self.nb_back_to_back, grouping=True, monetary=True)
            + sep
            + self.tr("Max combo: ")
            + locale.format("%i", self.max_combo, grouping=True, monetary=True)
            + sep
            + self.tr("Combos: ")
            + locale.format("%i", self.combos_total, grouping=True, monetary=True)
        )
        if full_stats:
            minutes = self.chronometer / 60
            text += (
                "\n"
                + sep
                + self.tr("Lines per minute: {:.1f}").format(
                    self.complete_lines_total / minutes
                )
                + sep
                + self.tr("Tetrominos locked down: ")
                + locale.format("%i", self.nb_tetro, grouping=True, monetary=True)
                + sep
                + self.tr("Tetrominos per minute: {:.1f}").format(
                    self.nb_tetro / minutes
                )
                + sep
            )
            text += sep.join(
                score_type["name"]
                + ": "
                + locale.format("%i", nb, grouping=True, monetary=True)
                for score_type, nb in tuple(zip(self.SCORES, self.lines_stats))[1:]
            )
        return text

    def resizeEvent(self, event):
        self.font = QtGui.QFont("PixelCaps!", Block.side / 3.5)


class AspectRatioWidget(QtWidgets.QWidget):
    """
    Keeps aspect ratio of child widget on resize
    https://stackoverflow.com/questions/48043469/how-to-lock-aspect-ratio-while-resizing-the-window
    """

    def __init__(self, widget, parent):
        super().__init__(parent)
        self.aspect_ratio = widget.size().width() / widget.size().height()
        self.setLayout(QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, self))
        #  add spacer, then widget, then spacer
        self.layout().addItem(QtWidgets.QSpacerItem(0, 0))
        self.layout().addWidget(widget)
        self.layout().addItem(QtWidgets.QSpacerItem(0, 0))

    def resizeEvent(self, e):
        w = e.size().width()
        h = e.size().height()

        if w / h > self.aspect_ratio:  # too wide
            self.layout().setDirection(QtWidgets.QBoxLayout.LeftToRight)
            widget_stretch = h * self.aspect_ratio
            outer_stretch = (w - widget_stretch) / 2 + 0.5
        else:  # too tall
            self.layout().setDirection(QtWidgets.QBoxLayout.TopToBottom)
            widget_stretch = w / self.aspect_ratio
            outer_stretch = (h - widget_stretch) / 2 + 0.5

        self.layout().setStretch(0, outer_stretch)
        self.layout().setStretch(1, widget_stretch)
        self.layout().setStretch(2, outer_stretch)


class Frames(QtWidgets.QWidget):
    """
    Display Hold queue, Matrix, Next piece, Next queue and Stats.
    Manage interactions between them.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        self.playing = False
        self.paused = False

        self.backgrounds = tuple(
            QtGui.QImage(os.path.join(BG_IMAGE_DIR, entry.name))
            for entry in os.scandir(BG_IMAGE_DIR)
            if entry.is_file() and ".jpg" in entry.name
        )
        self.reset_backgrounds()

        self.load_music()

        self.hold_queue = HoldQueue(self)
        self.board = Matrix(self)
        self.next_piece = Grid(self)
        self.stats = Stats(self)
        self.next_queue = NextQueue(self)

        self.matrices = (self.hold_queue, self.board, self.next_piece)
        self.columns = sum(matrix.COLUMNS + 1 for matrix in self.matrices) + 1
        self.rows = self.board.ROWS + 3

        w = QtWidgets.QWidget(self)
        w.setStyleSheet("background-color: transparent")
        grid = QtWidgets.QGridLayout()
        for x in range(self.rows):
            grid.setRowStretch(x, 1)
        for y in range(self.columns):
            grid.setColumnStretch(y, 1)
        grid.setSpacing(0)
        x, y = 1, 1
        grid.addWidget(
            self.hold_queue, y, x, self.hold_queue.ROWS, self.hold_queue.COLUMNS + 1
        )
        x += self.hold_queue.COLUMNS + 1
        grid.addWidget(self.board, y, x, self.board.ROWS + 2, self.board.COLUMNS + 1)
        x += self.board.COLUMNS + 1
        grid.addWidget(
            self.next_piece, y, x, self.next_piece.ROWS, self.next_piece.COLUMNS + 1
        )
        x, y = 0, self.hold_queue.ROWS + 2
        grid.addWidget(self.stats, y, x, self.stats.ROWS, self.stats.COLUMNS + 1)
        x += self.stats.COLUMNS + self.board.COLUMNS + 3
        grid.addWidget(
            self.next_queue, y, x, self.next_queue.ROWS, self.next_queue.COLUMNS + 1
        )
        w.setLayout(grid)
        w.resize(self.columns, self.rows)
        asw = AspectRatioWidget(w, self)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(asw)
        self.setLayout(layout)

        self.stats.temporary_text.connect(self.board.show_temporary_text)
        self.board.drop_signal.connect(self.stats.update_drop_score)
        self.board.lock_signal.connect(self.stats.update_score)

    def load_music(self):
        playlist = QtMultimedia.QMediaPlaylist(self)
        for entry in os.scandir(SOUNDS_DIR):
            if entry.is_file() and ".mp3" in entry.name:
                music_path = QtMultimedia.QMediaContent(
                    QtCore.QUrl.fromLocalFile(
                        os.path.join(SOUNDS_DIR, entry.name)
                    )
                )
                playlist.addMedia(music_path)
        playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Loop)
        self.music = QtMultimedia.QMediaPlayer(self)
        self.music.setAudioRole(QtMultimedia.QAudio.GameRole)
        self.music.setPlaylist(playlist)
        self.music.setVolume(settings[s.SOUND][s.MUSIC_VOLUME])

    def resizeEvent(self, event):
        Block.side = 0.9 * min(self.width() // self.columns, self.height() // self.rows)
        self.resize_bg_image()

    def resize_bg_image(self):
        self.resized_bg_image = QtGui.QPixmap.fromImage(self.bg_image)
        self.resized_bg_image = self.resized_bg_image.scaled(
            self.size(),
            QtCore.Qt.KeepAspectRatioByExpanding,
            QtCore.Qt.SmoothTransformation,
        )
        self.resized_bg_image = self.resized_bg_image.copy(
            (self.resized_bg_image.width() - self.width()) // 2,
            (self.resized_bg_image.height() - self.height()) // 2,
            self.width(),
            self.height(),
        )

    def reset_backgrounds(self):
        self.backgrounds_cycle = itertools.cycle(self.backgrounds)
        self.set_new_background()

    def set_new_background(self):
        self.bg_image = QtGui.QImage(next(self.backgrounds_cycle))
        self.resize_bg_image()

    def new_game(self):
        if self.playing:
            answer = QtWidgets.QMessageBox.question(
                self,
                self.tr("New game"),
                self.tr("A game is in progress.\n" "Do you want to abord it?"),
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel,
            )
            if answer == QtWidgets.QMessageBox.Cancel:
                self.pause(False)
                return
            self.music.stop()

        self.reset_backgrounds()
        self.stats.level, ok = QtWidgets.QInputDialog.getInt(
            self,
            self.tr("New game"),
            self.tr("Start level:"),
            1,
            1,
            15,
            flags=QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint,
        )
        if not ok:
            return

        self.playing = True
        self.music.play()
        self.hold_queue.piece = None
        self.stats.new_game()
        self.board.new_game()
        self.next_queue.pieces = [Tetromino() for _ in range(5)]
        self.next_queue.insert_pieces()
        self.next_piece.insert(Tetromino())
        self.pause(False)
        self.new_level()

    def new_level(self):
        self.set_new_background()
        level = self.stats.new_level()
        self.board.new_level(level)
        self.new_piece()

    def new_piece(self):
        if self.stats.goal <= 0:
            self.new_level()
        self.board.insert(self.next_piece.piece)
        self.board.lock_wait()
        self.next_piece.insert(self.next_queue.pieces[0])
        self.next_queue.new_piece()
        self.hold_enabled = settings[s.OTHER][s.HOLD_ENABLED]
        self.update()

        if not self.board.piece.move(0, 0):
            self.game_over()
            return

        self.board.fall_timer.start(self.board.speed)

    def pause(self, paused):
        if not self.playing:
            return

        if paused:
            self.paused = True
            self.update()
            self.board.fall_timer.stop()
            self.stats.clock.stop()
            self.board.auto_repeat_timer.stop()
            self.music.pause()
        else:
            self.board.text = ""
            self.update()
            QtCore.QTimer.singleShot(1000, self.resume)

    def resume(self):
        self.paused = False
        self.update()
        self.board.fall_timer.start(self.board.speed)
        self.stats.clock.start(1000)
        self.board.auto_repeat_timer.start(settings[s.DELAYS][s.AUTO_REPEAT_RATE])
        self.music.play()

    def hold(self):
        """
        Using the Hold command places the Tetrimino in play into the Hold Queue.
        The previously held Tetrimino (if one exists) will then start falling
        from the top of the Matrix,
        beginning from its generation position and North Facing orientation.
        Only one Tetrimino may be held at a time.
        A Lock Down must take place between Holds.
        For example, at the beginning, the first Tetrimino is generated and begins to fall.
        The player decides to hold this Tetrimino.
        Immediately the Next Tetrimino is generated from the Next Queue and begins to fall.
        The player must first Lock Down this Tetrimino before holding another Tetrimino.
        In other words, you may not Hold the same Tetrimino more than once.
        """

        if not self.hold_enabled:
            return

        piece = self.hold_queue.piece
        if piece:
            self.hold_queue.insert(self.board.piece)
            self.board.insert(piece)
            self.update()
        else:
            self.hold_queue.insert(self.board.piece)
            self.new_piece()
        self.hold_enabled = False

    def game_over(self):
        self.board.fall_timer.stop()
        self.stats.clock.stop()
        self.board.auto_repeat_timer.stop()
        self.music.stop()
        self.playing = False
        self.board.game_over = True
        if self.stats.score_total == self.stats.high_score:
            text = self.tr("Congratulations!\nYou have the high score!") + "\n\n"
        else:
            text = ""
        text += self.stats.text(full_stats=True)
        qsettings.setValue(self.tr("High score"), self.stats.high_score)
        QtWidgets.QMessageBox.information(self, self.tr("Game over"), text)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(self.rect(), self.resized_bg_image)


class KeyButton(QtWidgets.QPushButton):
    """ Button widget capturing key name on focus """

    names = {
        value: name.replace("Key_", "")
        for name, value in QtCore.Qt.__dict__.items()
        if "Key_" in name
    }

    def __init__(self, *args):
        super().__init__(*args)

    def keyPressEvent(self, event):
        key = event.key()
        self.setText(self.names[key])


class SettingsGroup(QtWidgets.QGroupBox):
    """ Group box of a type of settings """

    def __init__(self, group, parent, cls):
        super().__init__(group, parent)
        layout = QtWidgets.QFormLayout(self)
        self.widgets = {}
        for setting, value in settings[group].items():
            if cls == KeyButton:
                widget = KeyButton(value)
            elif cls == QtWidgets.QCheckBox:
                widget = QtWidgets.QCheckBox(setting)
                widget.setChecked(value)
            elif cls == QtWidgets.QSpinBox:
                widget = QtWidgets.QSpinBox()
                widget.setRange(0, 1000)
                widget.setValue(value)
                widget.setSuffix(" ms")
            elif cls == QtWidgets.QSlider:
                widget = QtWidgets.QSlider(QtCore.Qt.Horizontal)
                widget.setValue(value)
            if cls == QtWidgets.QCheckBox:
                layout.addRow(widget)
            else:
                layout.addRow(setting, widget)
            self.widgets[setting] = widget
        self.setLayout(layout)


class SettingsDialog(QtWidgets.QDialog):
    """ Show settings dialog """

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Settings"))
        self.setModal(True)

        vlayout = QtWidgets.QVBoxLayout()

        self.groups = {}
        self.groups[s.KEYBOARD] = SettingsGroup(s.KEYBOARD, self, KeyButton)
        self.groups[s.DELAYS] = SettingsGroup(s.DELAYS, self, QtWidgets.QSpinBox)
        self.groups[s.SOUND] = SettingsGroup(s.SOUND, self, QtWidgets.QSlider)
        self.groups[s.OTHER] = SettingsGroup(s.OTHER, self, QtWidgets.QCheckBox)

        for group in self.groups.values():
            vlayout.addWidget(group)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.ok)
        buttons.rejected.connect(self.close)
        vlayout.addWidget(buttons)

        self.groups[s.SOUND].widgets[s.MUSIC_VOLUME].valueChanged.connect(
            parent.frames.music.setVolume
        )

        self.setLayout(vlayout)
        self.show()

    def ok(self):
        """ Save settings """

        for group, elements in self.groups.items():
            for setting, widget in elements.widgets.items():
                if isinstance(widget, KeyButton):
                    value = widget.text()
                elif isinstance(widget, QtWidgets.QCheckBox):
                    value = widget.isChecked()
                elif isinstance(widget, QtWidgets.QSpinBox):
                    value = widget.value()
                elif isinstance(widget, QtWidgets.QSlider):
                    value = widget.value()
                settings[group][setting] = value
                qsettings.setValue(group + "/" + setting, value)
        self.close()


class SettingStrings(QtCore.QObject):
    """
    Setting string for translation
    """

    def __init__(self):
        super().__init__()

        self.KEYBOARD = self.tr("Keyboard settings")
        self.MOVE_LEFT = self.tr("Move left")
        self.MOVE_RIGHT = self.tr("Move right")
        self.ROTATE_CLOCKWISE = self.tr("Rotate clockwise")
        self.ROTATE_COUNTERCLOCKWISE = self.tr("Rotate counterclockwise")
        self.SOFT_DROP = self.tr("Soft drop")
        self.HARD_DROP = self.tr("Hard drop")
        self.HOLD = self.tr("Hold")
        self.PAUSE = self.tr("Pause")
        self.OTHER = self.tr("Other settings")

        self.DELAYS = self.tr("Delays")
        self.AUTO_SHIFT_DELAY = self.tr("Auto-shift delay")
        self.AUTO_REPEAT_RATE = self.tr("Auto-repeat rate")

        self.SOUND = self.tr("Sound")
        self.MUSIC_VOLUME = self.tr("Music volume")
        self.EFFECTS_VOLUME = self.tr("Effects volume")

        self.GHOST = self.tr("Show ghost piece")
        self.SHOW_NEXT_QUEUE = self.tr("Show next queue")
        self.HOLD_ENABLED = self.tr("Hold enabled")


class Window(QtWidgets.QMainWindow):
    """ Main window """

    def __init__(self):
        self.set_locale()

        super().__init__()
        self.setWindowTitle(__title__.upper())
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        # Windows' taskbar icon
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                ".".join((__author__, __title__, __version__))
            )
        except AttributeError:
            pass

        self.load_settings()

        # Stylesheet
        try:
            import qdarkstyle
        except ImportError:
            pass
        else:
            self.setStyleSheet(qdarkstyle.load_stylesheet_from_environment())

        for font_name in "maass slicer Italic.ttf", "PixelCaps!.otf":
            QtGui.QFontDatabase.addApplicationFont(
                os.path.join(FONTS_DIR, font_name)
            )

        self.frames = Frames(self)
        self.setCentralWidget(self.frames)
        self.hold_queue = self.frames.hold_queue
        self.board = self.frames.board
        self.stats = self.frames.stats

        self.menu = self.menuBar()

        geometry = qsettings.value("WindowGeometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(839, 807)
        self.setWindowState(
            QtCore.Qt.WindowStates(
                int(qsettings.value("WindowState", QtCore.Qt.WindowActive))
            )
        )

        self.show()
        self.frames.new_game()

    def set_locale(self):
        app = QtWidgets.QApplication.instance()

        # Set appropriate thounsand separator characters
        locale.setlocale(locale.LC_ALL, "")
        # Qt
        language = QtCore.QLocale.system().name()[:2]

        qt_translator = QtCore.QTranslator(app)
        qt_translation_path = QtCore.QLibraryInfo.location(
            QtCore.QLibraryInfo.TranslationsPath
        )
        if qt_translator.load("qt_" + language, qt_translation_path):
            app.installTranslator(qt_translator)

        tetris2000_translator = QtCore.QTranslator(app)
        if tetris2000_translator.load(language, LOCALE_PATH):
            app.installTranslator(tetris2000_translator)

    def load_settings(self):
        global qsettings
        qsettings = QtCore.QSettings(__author__, __title__)
        global s
        s = SettingStrings()
        global settings
        settings = collections.OrderedDict(
            [
                (
                    s.KEYBOARD,
                    collections.OrderedDict(
                        [
                            (
                                s.MOVE_LEFT,
                                qsettings.value(s.KEYBOARD + "/" + s.MOVE_LEFT, "Left"),
                            ),
                            (
                                s.MOVE_RIGHT,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.MOVE_RIGHT, "Right"
                                ),
                            ),
                            (
                                s.ROTATE_CLOCKWISE,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.ROTATE_CLOCKWISE, "Up"
                                ),
                            ),
                            (
                                s.ROTATE_COUNTERCLOCKWISE,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.ROTATE_COUNTERCLOCKWISE,
                                    "Control",
                                ),
                            ),
                            (
                                s.SOFT_DROP,
                                qsettings.value(s.KEYBOARD + "/" + s.SOFT_DROP, "Down"),
                            ),
                            (
                                s.HARD_DROP,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.HARD_DROP, "Space"
                                ),
                            ),
                            (
                                s.HOLD,
                                qsettings.value(s.KEYBOARD + "/" + s.HOLD, "Shift"),
                            ),
                            (
                                s.PAUSE,
                                qsettings.value(s.KEYBOARD + "/" + s.PAUSE, "Escape"),
                            ),
                        ]
                    ),
                ),
                (
                    s.DELAYS,
                    collections.OrderedDict(
                        [
                            (
                                s.AUTO_SHIFT_DELAY,
                                int(
                                    qsettings.value(
                                        s.DELAYS + "/" + s.AUTO_SHIFT_DELAY, 170
                                    )
                                ),
                            ),
                            (
                                s.AUTO_REPEAT_RATE,
                                int(
                                    qsettings.value(
                                        s.DELAYS + "/" + s.AUTO_REPEAT_RATE, 20
                                    )
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    s.SOUND,
                    collections.OrderedDict(
                        [
                            (
                                s.MUSIC_VOLUME,
                                int(
                                    qsettings.value(s.SOUND + "/" + s.MUSIC_VOLUME, 25)
                                ),
                            ),
                            (
                                s.EFFECTS_VOLUME,
                                int(
                                    qsettings.value(
                                        s.SOUND + "/" + s.EFFECTS_VOLUME, 50
                                    )
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    s.OTHER,
                    collections.OrderedDict(
                        [
                            (
                                s.GHOST,
                                bool(qsettings.value(s.OTHER + "/" + s.GHOST, True)),
                            ),
                            (
                                s.SHOW_NEXT_QUEUE,
                                bool(
                                    qsettings.value(
                                        s.OTHER + "/" + s.SHOW_NEXT_QUEUE, True
                                    )
                                ),
                            ),
                            (
                                s.HOLD_ENABLED,
                                bool(
                                    qsettings.value(
                                        s.OTHER + "/" + s.HOLD_ENABLED, True
                                    )
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        )

    def menuBar(self):
        menu = super().menuBar()

        new_game_action = QtWidgets.QAction(self.tr("&New game"), self)
        new_game_action.triggered.connect(self.frames.new_game)
        menu.addAction(new_game_action)

        settings_action = QtWidgets.QAction(self.tr("&Settings"), self)
        settings_action.triggered.connect(self.show_settings_dialog)
        menu.addAction(settings_action)

        about_action = QtWidgets.QAction(self.tr("&About"), self)
        about_action.triggered.connect(self.about)
        menu.addAction(about_action)
        return menu

    def show_settings_dialog(self):
        SettingsDialog(self).exec_()
        if self.frames.music.volume() and self.frames.playing:
            self.frames.music.play()
        else:
            self.frames.music.pause()
        self.frames.board.apply_settings()
        self.frames.stats.line_clear_sound.setVolume(
            settings[s.SOUND][s.EFFECTS_VOLUME]
        )
        self.frames.stats.tetris_sound.setVolume(settings[s.SOUND][s.EFFECTS_VOLUME])
        if self.frames.playing:
            self.frames.hold_enabled = settings[s.OTHER][s.HOLD_ENABLED]
            self.frames.pause(False)

    def about(self):
        QtWidgets.QMessageBox.about(
            self,
            __title__,
            self.tr(
                "Tetris® clone\n"
                "by Adrien Malingrey\n\n"
                "Tetris Game Design by Alekseï Pajitnov\n"
                "Graphism inspired by Tetris Effect\n"
                "Window style sheet by Colin Duquesnoy\n"
                "PixelCaps! font by Markus Koellmann\n"
                "Maass slicer font by Peter Wiegel\n"
                "Traditional song Korobeiniki arranged by Kobashik\n"
                "Sound effects made with voc-one by Simple-Media\n"
                "Background images found on xshyfc.com"
            ),
        )
        if self.playing:
            self.pause(False)

    def closeEvent(self, event):
        if self.frames.playing:
            answer = QtWidgets.QMessageBox.question(
                self,
                self.tr("Quit game?"),
                self.tr("A game is in progress.\nDo you want to abord it?"),
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel,
            )
            if answer == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                self.frames.pause(False)
                return

        self.frames.music.stop()

        #  Save settings
        qsettings.setValue(self.tr("High score"), self.stats.high_score)
        qsettings.setValue("WindowGeometry", self.saveGeometry())
        qsettings.setValue("WindowState", int(self.windowState()))


def main(args={}):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(args)
    win = Window()
    return app.exec_()


if __name__ == "__main__":
    return_code = main(sys.argv)
    sys.exit(return_code)
