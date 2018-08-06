#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Another TETRIS® clone
Tetris Game Design by Alexey Pajitnov.
Parts of comments issued from 2009 Tetris Design Guideline
"""


import sys

from qt5 import QtWidgets
from game_gui import Window
    
    
def play():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = Window()
    win.show()
    win.frames.new_game()
    sys.exit(app.exec_())

if __name__ == "__main__":
    play()