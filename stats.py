#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import locale
import time

import consts
from qt5 import QtWidgets, QtGui, QtCore, QtMultimedia
from settings import qsettings
from block import Block



class Stats(QtWidgets.QWidget):
    """
    Show informations relevant to the game being played is displayed on-screen.
    Looks for patterns made from Locked Down Blocks in the Matrix and calculate score.
    """

    ROWS = consts.STATS_ROWS
    COLUMNS = consts.STATS_COLUMNS
    TEXT_COLOR = consts.STATS_TEXT_COLOR

    temporary_text = QtCore.Signal(str)

    def __init__(self, frames):
        super().__init__(frames)
        self.frames = frames
        self.setStyleSheet("background-color: transparent")

        self.load_sfx()

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.text_options = QtGui.QTextOption(QtCore.Qt.AlignRight)
        self.text_options.setWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)

        self.clock = QtCore.QTimer()
        self.clock.timeout.connect(self.tick)

        self.high_score = int(qsettings.value(self.tr("High score"), 0))

    def load_sfx(self):
        self.line_clear_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(consts.LINE_CLEAR_SFX_PATH)
        self.line_clear_sfx.setSource(url)
        
        self.tetris_sfx = QtMultimedia.QSoundEffect(self)
        url = QtCore.QUrl.fromLocalFile(consts.TETRIS_SFX_PATH)
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
        if not self.frames.playing and not self.frames.matrix.game_over:
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
                + self.tr(": ")
                + locale.format("%i", nb, grouping=True, monetary=True)
                for score_type, nb in tuple(zip(consts.SCORES, self.lines_stats))[1:]
            )
        return text

    def resizeEvent(self, event):
        self.font = QtGui.QFont(consts.STATS_FONT_NAME, Block.side / 3.5)