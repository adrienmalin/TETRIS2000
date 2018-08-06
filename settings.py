#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import collections

import consts
from __version__ import __author__, __title__
from qt5 import QtWidgets, QtCore


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
            parent.frames.music.play)
        self.groups[s.SOUND].widgets[s.MUSIC_VOLUME].sliderReleased.connect(
            parent.frames.music.pause)
        
        self.groups[s.SOUND].widgets[s.SFX_VOLUME].sliderReleased.connect(
            parent.frames.stats.line_clear_sfx.play)
        
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


s = SettingStrings()

qsettings = QtCore.QSettings(__author__, __title__)

settings = collections.OrderedDict(
    [
        (
            s.KEYBOARD,
            collections.OrderedDict(
                [
                    (
                        s.MOVE_LEFT,
                        qsettings.value(s.KEYBOARD + "/" + s.MOVE_LEFT, consts.DEFAULT_MOVE_LEFT_KEY),
                    ),
                    (
                        s.MOVE_RIGHT,
                        qsettings.value(
                            s.KEYBOARD + "/" + s.MOVE_RIGHT, consts.DEFAULT_MOVE_RIGHT_KEY
                        ),
                    ),
                    (
                        s.ROTATE_CLOCKWISE,
                        qsettings.value(
                            s.KEYBOARD + "/" + s.ROTATE_CLOCKWISE, consts.DEFAULT_ROTATE_CLOCKWISE_KEY
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
                        qsettings.value(s.KEYBOARD + "/" + s.SOFT_DROP, consts.DEFAULT_SOFT_DROP_KEY),
                    ),
                    (
                        s.HARD_DROP,
                        qsettings.value(
                            s.KEYBOARD + "/" + s.HARD_DROP, consts.DEFAULT_HARD_DROP_KEY
                        ),
                    ),
                    (
                        s.HOLD,
                        qsettings.value(s.KEYBOARD + "/" + s.HOLD, consts.DEFAULT_HOLD_KEY),
                    ),
                    (
                        s.PAUSE,
                        qsettings.value(s.KEYBOARD + "/" + s.PAUSE, consts.DEFAULT_PAUSE_KEY),
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
                                s.DELAYS + "/" + s.AUTO_SHIFT_DELAY, consts.DEFAULT_AUTO_SHIFT_DELAY
                            )
                        ),
                    ),
                    (
                        s.AUTO_REPEAT_RATE,
                        int(
                            qsettings.value(
                                s.DELAYS + "/" + s.AUTO_REPEAT_RATE, consts.DEFAULT_AUTO_REPEAT_RATE
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
                            qsettings.value(s.SOUND + "/" + s.MUSIC_VOLUME, consts.DEFAUT_MUSIC_VOLUME)
                        ),
                    ),
                    (
                        s.SFX_VOLUME,
                        int(
                            qsettings.value(
                                s.SOUND + "/" + s.SFX_VOLUME, consts.DEFAULT_SFX_VOLUME
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
                        bool(qsettings.value(s.OTHER + "/" + s.GHOST, consts.DEFAULT_SHOW_GHOST)),
                    ),
                    (
                        s.SHOW_NEXT_QUEUE,
                        bool(
                            qsettings.value(
                                s.OTHER + "/" + s.SHOW_NEXT_QUEUE, consts.DEFAULT_SHOW_NEXT_QUEUE
                            )
                        ),
                    ),
                    (
                        s.HOLD_ENABLED,
                        bool(
                            qsettings.value(
                                s.OTHER + "/" + s.HOLD_ENABLED, consts.DEFAULT_HOLD_ENABLED
                            )
                        ),
                    ),
                ]
            ),
        ),
    ]
)