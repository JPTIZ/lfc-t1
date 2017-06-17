'''Module for main window.'''
import os
import re

import kivy
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.clock import Clock
from functools import partial

from gui.dialogs import SaveDialog, LoadDialog, InputDialog, ConfirmDialog
from dfa import DFA


class TableRow(BoxLayout):
    pass


class TableCell(Label):
    pass


class TableHeader(Label):
    pass


class AutomataTab(TabbedPanelItem):
    pass


class MainWindow(Widget):
    default_dir = ObjectProperty(os.getcwd())
    load = ObjectProperty(None)
    save = ObjectProperty(None)
    automatas = ObjectProperty([])

    def new_automata(self):
        automata = DFA.create(initial_state='q0',
                              transitions={},
                              final_states={})
        self.automatas.append(automata)
        new_tab = AutomataTab(text='Automata{}'.format(len(self.automatas)))
        new_tab.automata = automata
        self.ids.automata_tabs.add_widget(new_tab)
        self.ids.automata_tabs.switch_to(new_tab)
        Clock.schedule_once(partial(new_tab.ids.tabs.switch_to, new_tab.ids.transition_tab))
        self.ids.btn_close.disabled = False

    def current_tab(self):
        return self.ids.automata_tabs.current_tab

    def close_current(self):
        current = self.current_tab()
        tabs = self.ids.automata_tabs
        index = tabs.tab_list.index(current)
        self.automatas.remove(current.automata)
        tabs.remove_widget(current)
        if len(tabs.tab_list) > 0:
            tabs.switch_to(tabs.tab_list[index])
        else:
            tabs.clear_widgets()
            self.ids.btn_close.disabled = True

    def load_file(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, default_dir=self.default_dir)
        self._popup = Popup(title='Load', content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def save_file(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup, default_dir=self.default_dir)
        self._popup = Popup(title='Save', content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def open_input_dialog(self, title, action):
        content = InputDialog(pressed_ok=action)
        self._popup = Popup(title=title, content=content, size_hint=(None, None), size=(320, 92))
        self._popup.open()
        content.ids.input_box.focus = True

    def on_add_symbol(self):
        self.open_input_dialog('Add symbol', self.add_symbol)

    def current_transition_table(self):
        return self.ids.transition_table

    def add_symbol(self, symbol):
        self.dismiss_popup()
        transition_table = self.current_transition_table()
        transition_table.width += 48
        rows = transition_table.children
        header = False
        for row in reversed(rows):
            if not header:
                row.add_widget(TableHeader(text=symbol))
                header = True
            else:
                row.add_widget(TableCell(text='-'))
        self.ids.btn_close.enabled = False

    def remake_table(self):
        transition_table = self.current_transition_table()
        transition_table.clear_widgets()

        header = TableRow()
        header.add_widget(TableHeader(text='q'))
        transition_table.add_widget(header)

        rows = {}
        if self.automata:
            for char in self.automata.alphabet:
                header.add_widget(TableHeader(text=char))
            for state in self.automata.states:
                row = TableRow()
                rows[state] = [row]
                for char in self.automata.alphabet:
                    rows[state].append([])
                print(rows[state])
                state_name = state
                if state in self.automata.final_states:
                    state_name = '*' + state
                if state == self.automata.initial_state:
                    state_name = '→' + state
                row.add_widget(TableCell(text=state_name))
                for i, char in enumerate(self.automata.alphabet):
                    trans = self.automata.transitions[(state, char)]
                    if trans is not None:
                        rows[state][i + 1].append(trans)
                transition_table.add_widget(row)
            for state in rows:
                row = rows[state][1:]
                for i, char in enumerate(row):
                    if len(char) > 0:
                        rows[state][0].add_widget(TableCell(text=re.sub('\'', '', str(char))))
                    else:
                        rows[state][0].add_widget(TableCell(text='-'))

        transition_table.width = len(transition_table.children[0].children) * 48
        transition_table.height = len(transition_table.children) * 48


    def clear(self):
        transition_table = self.current_transition_table
        transition_table.clear_widgets()
        header = TableRow()
        header.add_widget(TableHeader(text='q'))
        transition_table.add_widget(header)
        first_row = TableRow()
        first_row.add_widget(TableCell(text='→S', editable=True))
        transition_table.add_widget(first_row)
        self.dismiss_popup()

    def show_clear_popup(self):
        content = ConfirmDialog(yes=self.clear, no=self.dismiss_popup)
        self._popup = Popup(title='Do you really want to clear the automata?', content=content, size_hint=(None, None), size=(320, 92))
        self._popup.open()
