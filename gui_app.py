import os
from pprint import pprint

from kivy.app import App
from kivy.clock import Clock
from functools import partial

from gui.main_window import MainWindow

from dfa import load_dfa


class FLViewer(App):
    def build(self):
        self.window = MainWindow(load=self.load, save=self.save)
        return self.window

    def load(self, path, filename):
        print('loading {}'.format(filename))
        for name in filename:
            automata = load_dfa(open(name))
            pprint(dict(automata._asdict()), width=-1)
            self.window.add_automata(automata, os.path.basename(name))
        self.window.default_dir = path
        self.window.dismiss_popup()

    def save(self, path, filename):
        print('(stub!) saving {}'.format(filename))
        self.window.default_dir = path
        self.window.dismiss_popup()


if __name__ == '__main__':
    FLViewer().run()
