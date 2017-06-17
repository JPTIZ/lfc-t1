import os

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
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


class InfoDialog(FloatLayout):
    message = ObjectProperty('')
    pressed_ok = ObjectProperty(None)


class TransitionEditDialog(FloatLayout):
    pressed_ok = ObjectProperty(None)
    value = ObjectProperty(None)


class ShortButton(Button):
    pass


class ShortSpinner(Spinner):
    option_cls = ObjectProperty(ShortButton)
