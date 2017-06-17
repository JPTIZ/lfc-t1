import os

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
    file_input = ObjectProperty(None)
    default_dir = ObjectProperty(os.getcwd())


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    default_dir = ObjectProperty(os.getcwd())


class InputDialog(FloatLayout):
    pressed_ok = ObjectProperty(None)

class ConfirmDialog(FloatLayout):
    yes = ObjectProperty(None)
    no = ObjectProperty(None)
