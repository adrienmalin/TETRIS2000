#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import locale
import ctypes

import consts
from qt5 import QtWidgets, QtCore, QtGui
from __version__ import __title__, __author__, __version__
from settings import SettingsDialog, qsettings
from frames import Frames


class Window(QtWidgets.QMainWindow):
    """ Main window """

    def __init__(self):
        splash_screen = QtWidgets.QSplashScreen(
            QtGui.QPixmap(consts.SPLASH_SCREEN_PATH)
        )
        splash_screen.show()
        
        self.set_locale()

        super().__init__()
        self.setWindowTitle(__title__.upper())
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setWindowIcon(QtGui.QIcon(consts.ICON_PATH))
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
            self.setStyleSheet(qdarkstyle.load_stylesheet_from_environment())

        for font_path in consts.STATS_FONT_PATH, consts.MATRIX_FONT_PATH:
            QtGui.QFontDatabase.addApplicationFont(font_path)

        self.frames = Frames(self)
        self.setCentralWidget(self.frames)
        self.hold_queue = self.frames.hold_queue
        self.matrix = self.frames.matrix
        self.stats = self.frames.stats

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

        splash_screen.finish(self);

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
        if tetris2000_translator.load(language, consts.LOCALE_PATH):
            app.installTranslator(tetris2000_translator)

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
        qsettings.setValue(self.tr("High score"), self.stats.high_score)
        qsettings.setValue("WindowGeometry", self.saveGeometry())
        qsettings.setValue("WindowState", int(self.windowState()))