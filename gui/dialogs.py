'''Contains forward declarations of Dialog windows and their properties.'''
import os

from enum import Enum

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.properties import ObjectProperty


class Operation(Enum):
    '''Current available operations for automatas.'''
    MINIMIZE = 0


class SaveDialog(FloatLayout):
    '''A file saving dialog.'''
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
    file_input = ObjectProperty(None)
    default_dir = ObjectProperty(os.getcwd())


class LoadDialog(FloatLayout):
    '''A file loading dialog.'''
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    default_dir = ObjectProperty(os.getcwd())


class InputDialog(FloatLayout):
    '''Dialog for text input.'''
    pressed_ok = ObjectProperty(None)


class ConfirmDialog(FloatLayout):
    '''Y/N dialog.'''
    yes = ObjectProperty(None)
    no = ObjectProperty(None)


class InfoDialog(FloatLayout):
    '''Simple message dialog.'''
    message = ObjectProperty('')
    pressed_ok = ObjectProperty(None)


class TransitionEditDialog(FloatLayout):
    '''Dialog for transition editing.'''
    pressed_ok = ObjectProperty(None)
    value = ObjectProperty(None)


class ShortButton(Button):
    '''Half-width button.'''
    pass


class ShortSpinner(Spinner):
    '''Kivy's Spinner with half width.'''
    option_cls = ObjectProperty(ShortButton)


class OperationSelectDialog(FloatLayout):
    '''Dialog for user to select an operation to run in the automata.'''
    selected_operation = ObjectProperty(None)
    cancel = ObjectProperty(None)
