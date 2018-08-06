#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import itertools

import consts
from qt5 import QtWidgets, QtCore, QtGui, QtMultimedia
from settings import s, qsettings, settings
from block import Block
from tetromino import Tetromino
from grids import Grid, HoldQueue, NextQueue
from matrix import Matrix
from stats import Stats




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
        self.load_music()

        self.hold_queue = HoldQueue(self)
        self.matrix = Matrix(self)
        self.next_piece = Grid(self)
        self.stats = Stats(self)
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
        grid.addWidget(self.matrix, y, x, self.matrix.ROWS + consts.GRID_INVISIBLE_ROWS, self.matrix.COLUMNS + 2)
        x += self.matrix.COLUMNS + 3
        grid.addWidget(
            self.next_piece, y, x, self.next_piece.ROWS + 1, self.next_piece.COLUMNS + 2
        )
        x, y = 0, self.hold_queue.ROWS + 2
        grid.addWidget(self.stats, y, x, self.stats.ROWS, self.stats.COLUMNS + 1)
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
        
        self.set_background(os.path.join(consts.BG_IMAGE_DIR, consts.START_BG_IMAGE_NAME))
        
        self.apply_settings()

    def load_music(self):
        playlist = QtMultimedia.QMediaPlaylist(self)
        for entry in os.scandir(consts.MUSICS_DIR):
            path = os.path.join(consts.MUSICS_DIR, entry.name)
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
            self.matrix.rotate_sfx, self.matrix.wall_sfx,
            self.stats.line_clear_sfx, self.stats.tetris_sfx
        ):
            sfx.setVolume(settings[s.SOUND][s.SFX_VOLUME])

    def resizeEvent(self, event):
        Block.side = 0.9 * min(self.width() // self.columns, self.height() // self.rows)
        self.resize_bg_image()

    def reset_backgrounds(self):
        backgrounds_paths = (
            os.path.join(consts.BG_IMAGE_DIR, entry.name)
            for entry in os.scandir(consts.BG_IMAGE_DIR)
        )
        self.backgrounds_cycle = itertools.cycle(backgrounds_paths)

    def set_background(self, path):
        self.bg_image = QtGui.QImage(path)
        self.resize_bg_image()

    def resize_bg_image(self):
        self.resized_bg_image = QtGui.QPixmap.fromImage(self.bg_image)
        self.resized_bg_image = self.resized_bg_image.scaled(
            self.size(),
            QtCore.Qt.KeepAspectRatioByExpanding,
            QtCore.Qt.SmoothTransformation
        )
        self.resized_bg_image = self.resized_bg_image.copy(
            (self.resized_bg_image.width() - self.width()) // 2,
            (self.resized_bg_image.height() - self.height()) // 2,
            self.width(),
            self.height()
        )
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(
            self.rect(),
            self.resized_bg_image)
        
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
        self.set_background(next(self.backgrounds_cycle))
        level = self.stats.new_level()
        self.matrix.new_level(level)

    def new_piece(self):
        if self.stats.goal <= 0:
            self.new_level()
        self.matrix.insert(self.next_piece.piece)
        self.matrix.lock_wait()
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
                self.tr(
                    "Congratulations!\nYou have the high score: {}"
                ).format(
                    
                    locale.format("%i", self.stats.high_score, grouping=True, monetary=True)
                )
            )
            qsettings.setValue(self.tr("High score"), self.stats.high_score)
        else:
            msgbox.setText(
                self.tr(
                    "Score: {}\nHigh score: {}"
                ).format(
                    locale.format("%i", self.stats.score_total, grouping=True, monetary=True),
                    locale.format("%i", self.stats.high_score, grouping=True, monetary=True)
                )
            )
        msgbox.setDetailedText(self.stats.text(full_stats=True))
        msgbox.exec_()