#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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