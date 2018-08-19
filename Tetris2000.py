#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Another TETRIS® clone
Tetris Game Design by Alexey Pajitnov.
Parts of comments issued from 2009 Tetris Design Guideline
"""


import sys

from source.qt5 import QtWidgets
from source.game_gui import Window


app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
win = Window()
win.show()
win.frames.new_game()
sys.exit(app.exec_())