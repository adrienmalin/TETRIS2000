# -*- coding: utf-8 -*-
from inflection import camelize


class Pythonic:
    def __getattribute__(self, name):
        # Don't touch magic methods
        if "__" in name:
            return object.__getattribute__(self, name)
        
        # If class has a setter named "set" + CamelCased name,
        # assume attribute has a getter named camelCased name
        try:
            object.__getattribute__(self, "set" + camelize(name))  # setter
            getter = object.__getattribute__(self, camelize(name, False))
        except AttributeError:
            try:
                # Try camelCased attribute
                return object.__getattribute__(self, camelize(name, False))
            except AttributeError:
                # Else return attribute
                return object.__getattribute__(self, name)
        else:
            return getter()
    
    def __setattr__(self, name, value):
        # Use setter if exists
        try:
            setter = object.__getattribute__(self, "set" + camelize(name))
        except AttributeError:
            # Try setting camelCased attribute
            try:
                object.__setattr__(self, camelize(name, False))
            except AttributeError:
                # Else set attribute
                object.__setattr__(self, name)
        else:
            setter(value)


if __name__ == "__main__":
    # Test
    
    from PyQt5 import QtWidgets, QtCore
    
    
    class Point(QtCore.QPoint, Pythonic):
        pass
    
    
    p = Point(0, 0)
    p.x = 9
    p.y = 3
    assert p == Point(9, 3)
    
    

    class Window(QtWidgets.QWidget, Pythonic):
        def __init__(self):
            super().__init__()
            self.window_title = "I'm pythonic!"
            self.geometry = QtCore.QRect(300, 300, 400, 300)
            self.layout = HBoxLayout()
            self.layout << PushButton()
            
            
    class HBoxLayout(QtWidgets.QHBoxLayout, Pythonic):
        def __lshift__(self, widget):
            self.add_widget(widget)
            
    
    class PushButton(QtWidgets.QPushButton, Pythonic):
        def __init__(self):
            super().__init__()
            self.text = "Click me!"
            
    
    app = QtWidgets.QApplication([])
    win = Window()
    win.show()
    app.exec_()
    