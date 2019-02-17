#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
import collections
import itertools
import locale
import os
import time
import functools
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia
QtCore.Signal = QtCore.pyqtSignal

import consts
from consts import L, R, CLOCKWISE, COUNTERCLOCKWISE
from __version__ import __title__, __author__, __version__
from point import Point
from tetromino import Block, Tetromino, GhostPiece


class Grid(QtWidgets.QWidget):
    """
    Mother class of Hold queue, Matrix, Next piece, and Next queue
    """

    ROWS = consts.GRID_DEFAULT_ROWS + consts.GRID_INVISIBLE_ROWS
    COLUMNS = consts.GRID_DEFAULT_COLUMNS
    STARTING_POSITION = Point(
        consts.GRID_DEFAULT_COLUMNS // 2 - 1,
        consts.GRID_DEFAULT_ROWS // 2 + consts.GRID_INVISIBLE_ROWS,
    )
    GRIDLINE_COLOR = consts.GRID_GRIDLINE_COLOR
    HARD_DROP_MOVEMENT = consts.GRID_HARD_DROP_MOVEMENT
    SPOTLIGHT = Point(*consts.GRID_SPOTLIGHT)

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
        for y in (
            j * Block.side for j in range(consts.GRID_INVISIBLE_ROWS, self.ROWS + 1)
        ):
            painter.drawLine(self.left, y, self.right, y)

    def paint_piece(self, painter, piece):
        for mino in piece.minoes:
            mino.paint(painter, self.top_left_corner, self.spotlight)


class Matrix(Grid):
    """
    The rectangular arrangement of cells creating the active game area.
    Tetriminos fall from the top-middle just above the Skyline (off-screen) to the bottom.
    """

    ROWS = consts.MATRIX_ROWS + consts.GRID_INVISIBLE_ROWS
    COLUMNS = consts.MATRIX_COLUMNS
    STARTING_POSITION = Point(COLUMNS // 2 - 1, consts.GRID_INVISIBLE_ROWS - 1)
    TEXT_COLOR = consts.MATRIX_TEXT_COLOR

    drop_signal = QtCore.Signal(int)
    lock_signal = QtCore.Signal(int, str)

    def __init__(self, frames, app):
        super().__init__(frames)

        self.load_sfx(app)

        self.game_over = False
        self.text = ""
        self.temporary_texts = []

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.auto_repeat_delay = 0
        self.auto_repeat_timer = QtCore.QTimer()
        self.auto_repeat_timer.setTimerType(QtCore.Qt.PreciseTimer)
        self.auto_repeat_timer.timeout.connect(self.auto_repeat)
        self.fall_timer = QtCore.QTimer()
        self.fall_timer.timeout.connect(self.fall)
        self.lock_timer = QtCore.QTimer()
        self.lock_timer.timeout.connect(self.lock_phase)
        self.lock_timer.setSingleShot(True)

        self.cells = []

    def load_sfx(self, app):
        self.wall_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(app.get_resource(consts.WALL_SFX_PATH))
        self.wall_sfx.setSource(url)

        self.rotate_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(app.get_resource(consts.ROTATE_SFX_PATH))
        self.rotate_sfx.setSource(url)

        self.hard_drop_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(app.get_resource(consts.HARD_DROP_SFX_PATH))
        self.hard_drop_sfx.setSource(url)

    def new_game(self):
        self.game_over = False
        self.lock_delay = consts.LOCK_DELAY
        self.cells = [self.empty_row() for y in range(self.ROWS)]
        self.setFocus()
        self.actions_to_repeat = []
        self.wall_hit = False

    def new_level(self, level):
        self.show_temporary_text(self.tr("Level\n") + str(level))
        self.speed = consts.INITIAL_SPEED * (0.8 - ((level - 1) * 0.007)) ** (level - 1)
        self.fall_timer.start(self.speed)
        if level > 15:
            self.lock_delay = consts.LOCK_DELAY * (consts.AFTER_LVL_15_ACCELERATION ** (level-15))

    def empty_row(self):
        return [None for x in range(self.COLUMNS)]

    def is_empty_cell(self, coord):
        x, y = coord.x, coord.y
        return (
            0 <= x < self.COLUMNS
            and y < self.ROWS
            and not (0 <= y and self.cells[y][x])
        )

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
                self.auto_repeat_wait()
                self.actions_to_repeat.append(action)

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
                self.wall_hit = False
            elif not self.wall_hit:
                self.wall_hit = True
                self.wall_sfx.play()

        elif action == s.MOVE_RIGHT:
            if self.piece.move(R, 0):
                self.rotate_sfx.play()
                self.lock_wait()
                self.wall_hit = False
            elif not self.wall_hit:
                self.wall_hit = True
                self.wall_sfx.play()

        elif action == s.ROTATE_CLOCKWISE:
            if self.piece.rotate(direction=CLOCKWISE):
                self.rotate_sfx.play()
                self.lock_wait()
                self.wall_hit = False
            elif not self.wall_hit:
                self.wall_hit = True
                self.wall_sfx.play()

        elif action == s.ROTATE_COUNTERCLOCKWISE:
            if self.piece.rotate(direction=COUNTERCLOCKWISE):
                self.lock_wait()
                self.wall_hit = False
            elif not self.wall_hit:
                self.wall_hit = True
                self.wall_sfx.play()

        elif action == s.SOFT_DROP:
            if self.piece.soft_drop():
                self.lock_wait()
                self.drop_signal.emit(1)
                self.wall_hit = False
            else:
                self.lock_start()
                if not self.wall_hit:
                    self.wall_hit = True
                    self.wall_sfx.play()

        elif action == s.HARD_DROP:
            trail = self.piece.hard_drop()
            self.top_left_corner += Point(0, self.HARD_DROP_MOVEMENT * Block.side)
            self.drop_signal.emit(2 * trail)
            QtCore.QTimer.singleShot(consts.ANIMATION_DELAY, self.after_hard_drop)
            self.hard_drop_sfx.play()
            self.lock_phase()

        elif action == s.HOLD:
            self.frames.hold()

    def after_hard_drop(self):
        """ Reset the animation movement of the Matrix on a hard drop """
        self.top_left_corner -= Point(0, self.HARD_DROP_MOVEMENT * Block.side)

    def lock_start(self):
        if not self.lock_timer.isActive():
            self.lock_timer.start(self.lock_delay)
            for mino in self.piece.minoes:
                mino.shine(1)
            self.update()

    def lock_wait(self):
        if self.lock_timer.isActive():
            self.lock_timer.start(self.lock_delay)

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
                self.lock_start()

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

        if self.piece.move(0, 1):
            self.lock_wait()
            return

        self.wall_sfx.play()

        #  Enter minoes into the matrix
        for mino in self.piece.minoes:
            if mino.coord.y >= 0:
                self.cells[mino.coord.y][mino.coord.x] = mino
            mino.shine(glowing=2, delay=consts.ANIMATION_DELAY)
            QtCore.QTimer.singleShot(consts.ANIMATION_DELAY, self.update)
        self.update()

        if all(
            mino.coord.y < consts.GRID_INVISIBLE_ROWS for mino in self.piece.minoes
        ):
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
        self.lock_signal.emit(len(self.complete_lines), self.piece.t_spin())

        if self.complete_lines:
            self.fall_timer.stop()
            QtCore.QTimer.singleShot(consts.LINE_CLEAR_DELAY, self.eliminate_phase)
        else:
            self.frames.new_piece()

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
                    self.ghost = GhostPiece(self.piece)
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
                "\n\n\n" + "\n\n".join(self.temporary_texts),
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.temporary_text_font = QtGui.QFont(consts.MATRIX_FONT_NAME, Block.side)

    def show_temporary_text(self, text):
        self.temporary_texts.append(text.upper())
        self.font = self.temporary_text_font
        self.update()
        QtCore.QTimer.singleShot(consts.TEMPORARY_TEXT_DURATION, self.delete_text)

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
            piece.insert_into(self, self.STARTING_POSITION + Point(0, 3 * y - 4))

    def paintEvent(self, event=None):
        if not settings[s.OTHER][s.SHOW_NEXT_QUEUE]:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if not self.frames.paused:
            for piece in self.pieces:
                self.paint_piece(painter, piece)


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


class Stats(QtWidgets.QWidget):
    """
    Show informations relevant to the game being played is displayed on-screen.
    Looks for patterns made from Locked Down Blocks in the Matrix and calculate score.
    """

    ROWS = consts.STATS_ROWS
    COLUMNS = consts.STATS_COLUMNS
    TEXT_COLOR = consts.STATS_TEXT_COLOR

    temporary_text = QtCore.Signal(str)

    def __init__(self, frames, app):
        super().__init__(frames)
        self.frames = frames
        self.setStyleSheet("background-color: transparent")

        self.load_sfx(app)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.text_options = QtGui.QTextOption(QtCore.Qt.AlignRight)
        self.text_options.setWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)

        self.clock = QtCore.QTimer()
        self.clock.timeout.connect(self.tick)

        self.high_score = int(qsettings.value(self.tr("High score"), 0))

    def load_sfx(self, app):
        self.line_clear_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(app.get_resource(consts.LINE_CLEAR_SFX_PATH))
        self.line_clear_sfx.setSource(url)

        self.tetris_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(app.get_resource(consts.TETRIS_SFX_PATH))
        self.tetris_sfx.setSource(url)

    def new_game(self):
        self.level -= 1
        self.goal = 0
        self.complete_lines_total = 0
        self.score_total = 1
        self.t_spin_total = 0
        self.mini_t_spin_total = 0
        self.nb_back_to_back = 0
        self.back_to_back_scores = None
        self.max_back_to_back_score = 0
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

        score = consts.SCORES[nb_complete_lines][t_spin]

        if score:
            text = " ".join((t_spin, consts.SCORES[nb_complete_lines]["name"]))
            if (t_spin and nb_complete_lines) or nb_complete_lines == 4:
                self.tetris_sfx.play()
            elif t_spin or nb_complete_lines:
                self.line_clear_sfx.play()

            self.goal -= score
            score = 100 * self.level * score
            self.score_total += score

            self.temporary_text.emit(text + "\n{:n}".format(score))

        # ==============================================================================
        # Combo
        # Bonus for complete lines on each consecutive lock downs
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
                if self.combo == 1:
                    self.temporary_text.emit(
                        self.tr("COMBO\n{:n}").format(combo_score)
                    )
                else:
                    self.temporary_text.emit(
                        self.tr("COMBO x{:n}\n{:n}").format(self.combo, combo_score)
                    )
        else:
            self.combo = -1

        # ==============================================================================
        # Back-to_back sequence
        # Two major bonus actions, such as two Tetrises, performed without
        # a Single, Double, or Triple Line Clear occurring between them.
        # Bonus for Tetrises, T-Spin Line Clears, and Mini T-Spin Line Clears
        # performed consecutively in a B2B sequence.
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
                self.max_back_to_back_score = max(self.max_back_to_back_score, b2b_score)
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
        if not self.frames.playing and not self.frames.matrix.game_over:
            return

        painter = QtGui.QPainter(self)
        painter.setFont(self.font)
        painter.setPen(self.TEXT_COLOR)

        painter.drawText(
            QtCore.QRectF(self.rect()), self.text(sep="\n\n"), self.text_options
        )
        
    """
    Returns a strings representing number with the locale thousand separator
    """
    thousand_separated = functools.partial(locale.format, "%i", grouping=True, monetary=True)

    def text(self, full_stats=False, sep="\n"):
        text = (
            self.tr("Score: ") + self.thousand_separated(self.score_total) + sep
            + self.tr("High score: ") + self.thousand_separated(self.high_score) + sep
            + self.tr("Time: {}\n").format(
                time.strftime("%H:%M:%S", time.gmtime(self.chronometer))
            ) + sep
            + self.tr("Level: ") + self.thousand_separated(self.level) + sep
            + self.tr("Goal: ") + self.thousand_separated(self.goal) + sep
            + self.tr("Lines: ") + self.thousand_separated(self.complete_lines_total) + sep
            + self.tr("Mini T-Spins: ") + self.thousand_separated(self.mini_t_spin_total) + sep
            + self.tr("T-Spins: ") + self.thousand_separated(self.t_spin_total) + sep
            + self.tr("Back-to-backs: ") + self.thousand_separated(self.nb_back_to_back) + sep
            + self.tr("Max back-to-back score: ") + self.thousand_separated(self.max_back_to_back_score) + sep
            + self.tr("Max combo: ") + self.thousand_separated(self.max_combo) + sep
            + self.tr("Combos: ") + self.thousand_separated(self.combos_total)
        )
        if full_stats:
            minutes = self.chronometer / 60 or 1
            text += (
                "\n" + sep
                + self.tr("Lines per minute: {:.1f}").format(
                    self.complete_lines_total / minutes
                ) + sep
                + self.tr("Tetrominos locked down: ")
                + self.thousand_separated(self.nb_tetro)
                + sep
                + self.tr("Tetrominos per minute: {:.1f}").format(
                    self.nb_tetro / minutes
                )
                + sep
            )
            text += sep.join(
                score_type["name"] + self.tr(": ") + self.thousand_separated(nb)
                for score_type, nb in tuple(zip(consts.SCORES, self.lines_stats))[1:]
            )
        return text

    def resizeEvent(self, event):
        self.font = QtGui.QFont(consts.STATS_FONT_NAME, Block.side / 3.5)


class Frames(QtWidgets.QWidget):
    """
    Display Hold queue, Matrix, Next piece, Next queue and Stats.
    Manage interactions between them.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        self.playing = False
        self.paused = False
        self.load_music()

        self.hold_queue = HoldQueue(self)
        self.matrix = Matrix(self, app)
        self.next_piece = Grid(self)
        self.stats = Stats(self, app)
        self.next_queue = NextQueue(self)

        self.matrices = (self.hold_queue, self.matrix, self.next_piece)
        self.columns = sum(matrix.COLUMNS + 2 for matrix in self.matrices)
        self.rows = self.matrix.ROWS + consts.GRID_INVISIBLE_ROWS

        w = QtWidgets.QWidget(self)
        w.setStyleSheet("background-color: transparent")
        grid = QtWidgets.QGridLayout()
        for x in range(self.rows):
            grid.setRowStretch(x, 1)
        for y in range(self.columns):
            grid.setColumnStretch(y, 1)
        grid.setSpacing(0)
        x, y = 0, 0
        grid.addWidget(
            self.hold_queue, y, x, self.hold_queue.ROWS + 1, self.hold_queue.COLUMNS + 2
        )
        x += self.hold_queue.COLUMNS + 2
        grid.addWidget(
            self.matrix,
            y,
            x,
            self.matrix.ROWS + consts.GRID_INVISIBLE_ROWS,
            self.matrix.COLUMNS + 2,
        )
        x += self.matrix.COLUMNS + 3
        grid.addWidget(
            self.next_piece, y, x, self.next_piece.ROWS + 1, self.next_piece.COLUMNS + 2
        )
        x, y = 0, self.hold_queue.ROWS + 1
        grid.addWidget(self.stats, y + 1, x, self.stats.ROWS, self.stats.COLUMNS + 1)
        x += self.stats.COLUMNS + self.matrix.COLUMNS + 5
        grid.addWidget(
            self.next_queue, y, x, self.next_queue.ROWS, self.next_queue.COLUMNS + 2
        )
        w.setLayout(grid)
        w.resize(self.columns, self.rows)
        asw = AspectRatioWidget(w, self)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(asw)
        self.setLayout(layout)

        self.stats.temporary_text.connect(self.matrix.show_temporary_text)
        self.matrix.drop_signal.connect(self.stats.update_drop_score)
        self.matrix.lock_signal.connect(self.stats.update_score)

        self.bg_image = QtGui.QImage(
                os.path.join(app.get_resource(consts.START_BG_IMAGE_PATH))
        )
        self.resize_bg_image()
        
        self.apply_settings()

    def load_music(self):
        playlist = QtMultimedia.QMediaPlaylist(self)
        MUSICS_DIR = self.app.get_resource(consts.MUSICS_DIR)
        for entry in os.scandir(MUSICS_DIR):
            path = os.path.join(MUSICS_DIR, entry.name)
            url = QtCore.QUrl.fromLocalFile(path)
            music = QtMultimedia.QMediaContent(url)
            playlist.addMedia(music)
        playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Loop)
        self.music = QtMultimedia.QMediaPlayer(self)
        self.music.setAudioRole(QtMultimedia.QAudio.GameRole)
        self.music.setPlaylist(playlist)
        self.music.setVolume(settings[s.SOUND][s.MUSIC_VOLUME])

    def apply_settings(self):
        if self.music.volume() > 5 and self.playing:
            self.music.play()
        else:
            self.music.pause()

        if self.playing:
            self.hold_enabled = settings[s.OTHER][s.HOLD_ENABLED]
            self.pause(False)

        self.matrix.keys = {
            getattr(QtCore.Qt, "Key_" + name): action
            for action, name in settings[s.KEYBOARD].items()
        }
        self.matrix.auto_repeat_timer.start(settings[s.DELAYS][s.AUTO_REPEAT_RATE])
        self.matrix.spotlight = Matrix.SPOTLIGHT

        for sfx in (
            self.matrix.rotate_sfx,
            self.matrix.wall_sfx,
            self.stats.line_clear_sfx,
            self.stats.tetris_sfx,
        ):
            sfx.setVolume(settings[s.SOUND][s.SFX_VOLUME])

    def resizeEvent(self, event):
        Block.side = 0.9 * min(self.width() // self.columns, self.height() // self.rows)
        self.resize_bg_image()

    def reset_backgrounds(self):
        BG_IMAGE_DIR = self.app.get_resource(consts.BG_IMAGE_DIR)
        backgrounds = tuple(
            QtGui.QImage((os.path.join(BG_IMAGE_DIR, entry.name)))
            for entry in os.scandir(BG_IMAGE_DIR)
        )
        self.backgrounds_cycle = itertools.cycle(backgrounds)

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
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(self.rect(), self.resized_bg_image)

    def new_game(self):
        if self.playing:
            answer = QtWidgets.QMessageBox.question(
                self,
                self.tr("New game"),
                self.tr("A game is in progress.\nDo you want to abord it?"),
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
        self.load_music()
        self.music.play()
        self.hold_queue.piece = None
        self.stats.new_game()
        self.matrix.new_game()
        self.next_queue.pieces = [Tetromino() for _ in range(5)]
        self.next_queue.insert_pieces()
        self.next_piece.insert(Tetromino())
        self.pause(False)
        self.new_level()
        self.new_piece()

    def new_level(self):
        self.bg_image = QtGui.QImage(next(self.backgrounds_cycle))
        self.resize_bg_image()
        level = self.stats.new_level()
        self.matrix.new_level(level)

    def new_piece(self):
        if self.stats.goal <= 0:
            self.new_level()
        self.matrix.insert(self.next_piece.piece)
        self.next_piece.insert(self.next_queue.pieces[0])
        self.next_queue.new_piece()
        self.hold_enabled = settings[s.OTHER][s.HOLD_ENABLED]
        self.update()

        if not self.matrix.piece.move(0, 0):
            self.game_over()
            return

        self.matrix.fall_timer.start(self.matrix.speed)

    def pause(self, paused):
        if not self.playing:
            return

        if paused:
            self.paused = True
            self.update()
            self.matrix.fall_timer.stop()
            self.stats.clock.stop()
            self.matrix.auto_repeat_timer.stop()
            self.music.pause()
        else:
            self.matrix.text = ""
            self.update()
            QtCore.QTimer.singleShot(1000, self.resume)

    def resume(self):
        self.paused = False
        self.update()
        self.matrix.fall_timer.start(self.matrix.speed)
        self.stats.clock.start(1000)
        self.matrix.auto_repeat_timer.start(settings[s.DELAYS][s.AUTO_REPEAT_RATE])
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
            self.hold_queue.insert(self.matrix.piece)
            self.matrix.insert(piece)
            self.update()
        else:
            self.hold_queue.insert(self.matrix.piece)
            self.new_piece()
        self.hold_enabled = False

    def game_over(self):
        self.matrix.fall_timer.stop()
        self.stats.clock.stop()
        self.matrix.auto_repeat_timer.stop()
        self.music.stop()
        self.playing = False
        self.matrix.game_over = True
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setWindowTitle(self.tr("Game over"))
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        if self.stats.score_total == self.stats.high_score:
            msgbox.setText(
                self.tr("Congratulations!\nYou have the high score: {}").format(
                    locale.format(
                        "%i", self.stats.high_score, grouping=True, monetary=True
                    )
                )
            )
            qsettings.setValue(self.tr("High score"), self.stats.high_score)
        else:
            msgbox.setText(
                self.tr("Score: {}\nHigh score: {}").format(
                    locale.format(
                        "%i", self.stats.score_total, grouping=True, monetary=True
                    ),
                    locale.format(
                        "%i", self.stats.high_score, grouping=True, monetary=True
                    ),
                )
            )
        msgbox.setDetailedText(self.stats.text(full_stats=True))
        # Find and set default the "show details" button
        for button in msgbox.buttons():
            if msgbox.buttonRole(button) == QtWidgets.QMessageBox.ActionRole:
                msgbox.setDefaultButton(button)
        msgbox.exec_()


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
        self.SFX_VOLUME = self.tr("Effects volume")

        self.GHOST = self.tr("Show ghost piece")
        self.SHOW_NEXT_QUEUE = self.tr("Show next queue")
        self.HOLD_ENABLED = self.tr("Hold enabled")


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

        layout = QtWidgets.QGridLayout()

        self.groups = {}
        self.groups[s.KEYBOARD] = SettingsGroup(s.KEYBOARD, self, KeyButton)
        self.groups[s.DELAYS] = SettingsGroup(s.DELAYS, self, QtWidgets.QSpinBox)
        self.groups[s.SOUND] = SettingsGroup(s.SOUND, self, QtWidgets.QSlider)
        self.groups[s.OTHER] = SettingsGroup(s.OTHER, self, QtWidgets.QCheckBox)

        layout.addWidget(self.groups[s.KEYBOARD], 0, 0, 3, 1)
        layout.addWidget(self.groups[s.DELAYS], 0, 1)
        layout.addWidget(self.groups[s.SOUND], 1, 1)
        layout.addWidget(self.groups[s.OTHER], 2, 1)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.ok)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons, 3, 0, 1, 2)

        self.setLayout(layout)

        self.groups[s.SOUND].widgets[s.MUSIC_VOLUME].valueChanged.connect(
            parent.frames.music.setVolume
        )
        self.groups[s.SOUND].widgets[s.MUSIC_VOLUME].sliderPressed.connect(
            parent.frames.music.play
        )
        self.groups[s.SOUND].widgets[s.MUSIC_VOLUME].sliderReleased.connect(
            parent.frames.music.pause
        )

        self.groups[s.SOUND].widgets[s.SFX_VOLUME].sliderReleased.connect(
            parent.frames.stats.line_clear_sfx.play
        )

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


class Window(QtWidgets.QMainWindow):
    """ Main window """

    def __init__(self, app):
        splash_screen = QtWidgets.QSplashScreen(
            QtGui.QPixmap(app.get_resource(consts.SPLASH_SCREEN_PATH))
        )
        splash_screen.show()

        super().__init__()
        self.setWindowTitle(__title__.upper())
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.set_locale(app)

        self.load_settings()

        self.setWindowIcon(app.app_icon)
        # Windows' taskbar icon
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                ".".join((__author__, __title__, __version__))
            )
        except AttributeError:
            pass

        # Stylesheet
        try:
            import qdarkstyle
        except ImportError:
            pass
        else:
            os.environ['QT_API'] = 'pyqt5'
            self.setStyleSheet(qdarkstyle.load_stylesheet_from_environment())

        for font_path in consts.STATS_FONT_PATH, consts.MATRIX_FONT_PATH:
            QtGui.QFontDatabase.addApplicationFont(app.get_resource(font_path))

        self.frames = Frames(self, app)
        self.setCentralWidget(self.frames)

        self.menu = self.menuBar()

        geometry = qsettings.value("WindowGeometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(*consts.DEFAULT_WINDOW_SIZE)
        self.setWindowState(
            QtCore.Qt.WindowStates(
                int(qsettings.value("WindowState", QtCore.Qt.WindowActive))
            )
        )

        splash_screen.finish(self)
        
    def show(self):
        super().show()
        self.frames.new_game()

    def set_locale(self, app):
        qapp = QtWidgets.QApplication.instance()

        # Set appropriate thounsand separator characters
        locale.setlocale(locale.LC_ALL, "")
        # Qt
        language = QtCore.QLocale.system().name()[:2]

        qt_translator = QtCore.QTranslator(qapp)
        qt_translation_path = QtCore.QLibraryInfo.location(
            QtCore.QLibraryInfo.TranslationsPath
        )
        if qt_translator.load("qt_" + language, qt_translation_path):
            qapp.installTranslator(qt_translator)

        tetris2000_translator = QtCore.QTranslator(qapp)
        if tetris2000_translator.load(language, app.get_resource(consts.LOCALE_PATH)):
            qapp.installTranslator(tetris2000_translator)

    def load_settings(self):
        global s
        s = SettingStrings()
        global qsettings
        qsettings = QtCore.QSettings(__author__, __title__)
        global settings
        settings = collections.OrderedDict(
            [
                (
                    s.KEYBOARD,
                    collections.OrderedDict(
                        [
                            (
                                s.MOVE_LEFT,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.MOVE_LEFT,
                                    consts.DEFAULT_MOVE_LEFT_KEY,
                                ),
                            ),
                            (
                                s.MOVE_RIGHT,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.MOVE_RIGHT,
                                    consts.DEFAULT_MOVE_RIGHT_KEY,
                                ),
                            ),
                            (
                                s.ROTATE_CLOCKWISE,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.ROTATE_CLOCKWISE,
                                    consts.DEFAULT_ROTATE_CLOCKWISE_KEY,
                                ),
                            ),
                            (
                                s.ROTATE_COUNTERCLOCKWISE,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.ROTATE_COUNTERCLOCKWISE,
                                    consts.DEFAULT_ROTATE_COUNTERCLOCKWISE_KEY,
                                ),
                            ),
                            (
                                s.SOFT_DROP,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.SOFT_DROP,
                                    consts.DEFAULT_SOFT_DROP_KEY,
                                ),
                            ),
                            (
                                s.HARD_DROP,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.HARD_DROP,
                                    consts.DEFAULT_HARD_DROP_KEY,
                                ),
                            ),
                            (
                                s.HOLD,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.HOLD, consts.DEFAULT_HOLD_KEY
                                ),
                            ),
                            (
                                s.PAUSE,
                                qsettings.value(
                                    s.KEYBOARD + "/" + s.PAUSE, consts.DEFAULT_PAUSE_KEY
                                ),
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
                                        s.DELAYS + "/" + s.AUTO_SHIFT_DELAY,
                                        consts.DEFAULT_AUTO_SHIFT_DELAY,
                                    )
                                ),
                            ),
                            (
                                s.AUTO_REPEAT_RATE,
                                int(
                                    qsettings.value(
                                        s.DELAYS + "/" + s.AUTO_REPEAT_RATE,
                                        consts.DEFAULT_AUTO_REPEAT_RATE,
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
                                    qsettings.value(
                                        s.SOUND + "/" + s.MUSIC_VOLUME,
                                        consts.DEFAUT_MUSIC_VOLUME,
                                    )
                                ),
                            ),
                            (
                                s.SFX_VOLUME,
                                int(
                                    qsettings.value(
                                        s.SOUND + "/" + s.SFX_VOLUME,
                                        consts.DEFAULT_SFX_VOLUME,
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
                                bool(
                                    qsettings.value(
                                        s.OTHER + "/" + s.GHOST,
                                        consts.DEFAULT_SHOW_GHOST,
                                    )
                                ),
                            ),
                            (
                                s.SHOW_NEXT_QUEUE,
                                bool(
                                    qsettings.value(
                                        s.OTHER + "/" + s.SHOW_NEXT_QUEUE,
                                        consts.DEFAULT_SHOW_NEXT_QUEUE,
                                    )
                                ),
                            ),
                            (
                                s.HOLD_ENABLED,
                                bool(
                                    qsettings.value(
                                        s.OTHER + "/" + s.HOLD_ENABLED,
                                        consts.DEFAULT_HOLD_ENABLED,
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

        self.frames.apply_settings()

    def about(self):
        QtWidgets.QMessageBox.about(
            self,
            __title__,
            self.tr(
                """Tetris® clone by Adrien Malingrey

Tetris Game Design by Alekseï Pajitnov
Graphism inspired by Tetris Effect
Window style sheet: qdarkstyle by Colin Duquesnoy
Fonts by Markus Koellmann, Peter Wiegel
Images from:
OpenGameArt.org by beren77, Duion
Pexels.com by Min An, Jaymantri, Felix Mittermeier
Pixabay.com by LoganArt
Pixnio.com by Adrian Pelletier
Unsplash.com by Aron, Patrick Fore, Ilnur Kalimullin, Gabriel Garcia Marengo, Adnanta Raharja
StockSnap.io by Nathan Anderson, José Ignacio Pompé
Musics from ocremix.org by:
CheDDer Nardz, djpretzel, MkVaff, Sir_NutS, R3FORGED, Sir_NutS
Sound effects made with voc-one by Simple-Media"""
            ),
        )
        if self.frames.playing:
            self.frames.pause(False)

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
        qsettings.setValue(self.tr("High score"), self.frames.stats.high_score)
        qsettings.setValue("WindowGeometry", self.saveGeometry())
        qsettings.setValue("WindowState", int(self.windowState()))

