#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
from qtpy import QtGui


# Paths
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.dirname(PATH)
ICON_PATH = os.path.join(PATH, "icons", "icon.ico")
BG_IMAGE_DIR = os.path.join(PATH, "backgrounds")
START_BG_IMAGE_NAME = "01-spacefield_a-000.png"
MUSICS_DIR = os.path.join(PATH, "musics")
SFX_DIR = os.path.join(PATH, "sfx")
LINE_CLEAR_SFX_PATH = os.path.join(SFX_DIR, "line_clear.wav")
TETRIS_SFX_PATH = os.path.join(SFX_DIR, "tetris.wav")
ROTATE_SFX_PATH = os.path.join(SFX_DIR, "rotate.wav")
HARD_DROP_SFX_PATH = os.path.join(SFX_DIR, "hard_drop.wav")
WALL_SFX_PATH = os.path.join(SFX_DIR, "wall.wav")
LOCALE_PATH = os.path.join(PATH, "locale")
FONTS_DIR = os.path.join(PATH, "fonts")
STATS_FONT_PATH = os.path.join(FONTS_DIR, "PixelCaps!.otf")
STATS_FONT_NAME = "PixelCaps!"
MATRIX_FONT_PATH = os.path.join(FONTS_DIR, "maass slicer Italic.ttf")
MATRIX_FONT_NAME = "Maassslicer"

SPLASH_SCREEN_PATH = os.path.join(PATH, "icons", "splash_screen.png")

# Coordinates and direction
L, R, U, D = -1, 1, -1, 1  # Left, Right, Up, Down
CLOCKWISE, COUNTERCLOCKWISE = 1, -1

# Delays in milliseconds
ANIMATION_DELAY = 67
INITIAL_SPEED = 1000
ENTRY_DELAY = 80
LINE_CLEAR_DELAY = 80
LOCK_DELAY = 500
TEMPORARY_TEXT_DURATION = 1000
AFTER_LVL_15_ACCELERATION = 0.9

# Block Colors
BLOCK_BORDER_COLOR = QtGui.QColor(0, 159, 218, 255)
BLOCK_FILL_COLOR = QtGui.QColor(0, 159, 218, 25)
BLOCK_GLOWING_BORDER_COLOR = None
BLOCK_GLOWING_FILL_COLOR = QtGui.QColor(186, 211, 255, 70)
BLOCK_LIGHT_COLOR = QtGui.QColor(242, 255, 255, 40)
BLOCK_TRANSPARENT = QtGui.QColor(255, 255, 255, 0)
BLOCK_GLOWING = 0
BLOCK_INITIAL_SIDE = 20

GHOST_BLOCK_BORDER_COLOR = QtGui.QColor(135, 213, 255, 255)
GHOST_BLOCK_FILL_COLOR = None
GHOST_BLOCK_GLOWING_FILL_COLOR = QtGui.QColor(201, 149, 205, 255)
GHOST_BLOCK_GLOWING = 1

# Grid
GRID_INVISIBLE_ROWS = 3
GRID_DEFAULT_ROWS = 4
GRID_DEFAULT_COLUMNS = 6
GRID_GRIDLINE_COLOR = QtGui.QColor(255, 255, 255, 60)
GRID_HARD_DROP_MOVEMENT = 0.2
GRID_SPOTLIGHT = 0, 0

# Matrix
MATRIX_ROWS = 20
MATRIX_COLUMNS = 10
MATRIX_TEXT_COLOR = QtGui.QColor(204, 255, 255, 128)

# Next Queue
NEXT_QUEUE_ROWS = 16
NEXT_QUEUE_COLUMNS = 6

# Stats frame
STATS_ROWS = 15
STATS_COLUMNS = 6
STATS_TEXT_COLOR = QtGui.QColor(0, 159, 218, 128)
SCORES = (
    {"name": "", "": 0, "Mini T-Spin": 1, "T-Spin": 4},
    {"name": "Single", "": 1, "Mini T-Spin": 2, "T-Spin": 8},
    {"name": "Double", "": 3, "T-Spin": 12},
    {"name": "Triple", "": 5, "T-Spin": 16},
    {"name": "Tetris", "": 8},
)

# Default settings
DEFAULT_WINDOW_SIZE = 839, 807
# Key mapping
DEFAULT_MOVE_LEFT_KEY = "Left"
DEFAULT_MOVE_RIGHT_KEY = "Right"
DEFAULT_ROTATE_CLOCKWISE_KEY = "Up"
DEFAULT_ROTATE_COUNTERCLOCKWISE_KEY = "Control"
DEFAULT_SOFT_DROP_KEY = "Down"
DEFAULT_HARD_DROP_KEY = "Space"
DEFAULT_HOLD_KEY = "Shift"
DEFAULT_PAUSE_KEY = "Escape"
# Delays in milliseconds
DEFAULT_AUTO_SHIFT_DELAY = 170
DEFAULT_AUTO_REPEAT_RATE = 20
# Volume in percent
DEFAUT_MUSIC_VOLUME = 25
DEFAULT_SFX_VOLUME = 50
# Other
DEFAULT_SHOW_GHOST = True
DEFAULT_SHOW_NEXT_QUEUE = True
DEFAULT_HOLD_ENABLED = True
