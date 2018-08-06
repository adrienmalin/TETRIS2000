#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time

import consts
from consts import L, R, CLOCKWISE, COUNTERCLOCKWISE
from qt5 import QtGui, QtCore, QtMultimedia
from grids import Grid
from point import Point
from block import Block
from tetromino import GhostPiece
from settings import s, settings


class Matrix(Grid):
    """
    The rectangular arrangement of cells creating the active game area.
    Tetriminos fall from the top-middle just above the Skyline (off-screen) to the bottom.
    """

    ROWS = consts.MATRIX_ROWS + consts.GRID_INVISIBLE_ROWS
    COLUMNS = consts.MATRIX_COLUMNS
    STARTING_POSITION = Point(COLUMNS // 2, consts.GRID_INVISIBLE_ROWS - 1)
    TEXT_COLOR = consts.MATRIX_TEXT_COLOR

    drop_signal = QtCore.Signal(int)
    lock_signal = QtCore.Signal(int, str)

    def __init__(self, frames):
        super().__init__(frames)
        
        self.load_sfx()

        self.game_over = False
        self.text = ""
        self.temporary_texts = []

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.auto_repeat_delay = 0
        self.auto_repeat_timer = QtCore.QTimer()
        self.auto_repeat_timer.timeout.connect(self.auto_repeat)
        self.fall_timer = QtCore.QTimer()
        self.fall_timer.timeout.connect(self.fall)

        self.cells = []
        
    def load_sfx(self):
        self.wall_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(consts.WALL_SFX_PATH)
        self.wall_sfx.setSource(url)
        
        self.rotate_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(consts.ROTATE_SFX_PATH)
        self.rotate_sfx.setSource(url)
        
        self.hard_drop_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(consts.HARD_DROP_SFX_PATH)
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
            self.lock_delay *= 0.9

    def empty_row(self):
        return [None for x in range(self.COLUMNS)]

    def is_empty_cell(self, coord):
        x, y = coord.x(), coord.y()
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
                self.drop_signal.emit(1)
                self.wall_hit = False
            elif not self.wall_hit:
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
        
        self.wall_sfx.play()
        
        #  Enter minoes into the matrix
        for mino in self.piece.minoes:
            if mino.coord.y() >= 0:
                self.cells[mino.coord.y()][mino.coord.x()] = mino
            mino.shine(glowing=2, delay=consts.ANIMATION_DELAY)
        self.update()

        if all(mino.coord.y() < consts.GRID_INVISIBLE_ROWS for mino in self.piece.minoes):
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