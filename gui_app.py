'''Project's main module for GUI execution.'''
import os
from pprint import pprint

from kivy.app import App
from kivy.clock import Clock

from gui.main_window import MainWindow

from dfa import load_dfa, dump_dfa
from nfa import load_nfa, dump_nfa


class FLViewer(App):
    '''The Kivy App for Formal Languages Viewing.'''
    def build(self):
        '''Builds the app. Kivy-handled.'''
        self.window = MainWindow(load=self.load, save=self.save)
        return self.window

    def load(self, path, filename):
        '''Loads a JSON file with an automata definition.'''
        print('loading {}'.format(filename))
        for name in filename:
            try:
                with open(name) as fp:
                    automata = load_dfa(fp)
            except TypeError:
                with open(name) as fp:
                    automata = load_nfa(fp)
            pprint(dict(automata._asdict()), width=-1)
            self.window.add_automata(automata, os.path.basename(name))
        self.window.default_dir = path
        self.window.dismiss_popup()

    def save(self, path, filename_):
        '''Saves a JSON file with the window's current automata definition.'''
        print('saving {}'.format(filename))
        filename = os.path.join(path, filename_)
        pprint(dict(self.window.current_automata()._asdict()), width=-1)
        dump_dfa(fp=open(filename, mode='w'), dfa=self.window.current_automata())
        self.window.current_tab().text = filename_
        self.window.default_dir = path
        self.window.dismiss_popup()


if __name__ == '__main__':
    FLViewer().run()
