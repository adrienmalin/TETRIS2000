#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Another TETRIS® clone
Tetris Game Design by Alexey Pajitnov.
Parts of comments issued from 2009 Tetris Design Guideline
"""


from fbs_runtime.application_context import ApplicationContext
from game_gui import Window

import sys

class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext
    def run(self):                              # 2. Implement run()
        win = Window(self)
        win.show()
        return self.app.exec_()                 # 3. End run() with this line

if __name__ == '__main__':
    app = AppContext()                      # 4. Instantiate the subclass
    exit_code = app.run()                   # 5. Invoke run()
    sys.exit(exit_code)
