'''Module for main window.'''
from kivy.app import App
from kivy.uix.widget import Widget


class MainWindow(Widget):
    def new_automata(self):
        print('stub (new automata)')

    def load_file(self):
        print('stub (load file)')

    def add_symbol(self):
        self.ids.transition_table.cols += 1


class FLViewer(App):
    def build(self):
        return MainWindow()


if __name__ == '__main__':
    FLViewer().run()
