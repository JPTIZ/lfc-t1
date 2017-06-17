'''Module for main window.'''
import os
import re

import kivy
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.clock import Clock
from functools import partial

from gui.dialogs import (SaveDialog, LoadDialog, InputDialog, ConfirmDialog,
        TransitionEditDialog, ShortSpinner)
from gui.table import TableRow, TableCell, TableHeader
from dfa import DFA

from pprint import pprint


class AutomataTab(TabbedPanelItem):
    pass


def with_symbol(automata, symbol):
    transitions = automata.transitions
    for state in automata.states:
        transitions[(state, symbol)] = '-'
    return DFA.create(automata.initial_state,
                      transitions,
                      automata.final_states)

def with_state(automata, state):
    transitions = automata.transitions
    for symbol in automata.alphabet:
        transitions[(state, symbol)] = '-'
    return DFA.create(automata.initial_state,
                      transitions,
                      automata.final_states)


class MainWindow(Widget):
    default_dir = ObjectProperty(os.getcwd())
    load = ObjectProperty(None)
    save = ObjectProperty(None)
    automata_count = ObjectProperty(0)

    def current_tab(self):
        return self.ids.automata_tabs.current_tab

    def current_automata(self):
        return self.current_tab().automata

    def current_transition_table(self):
        return self.current_tab().ids.transition_table

    def new_automata(self):
        automata = DFA.create(initial_state='q0',
                              transitions={},
                              final_states={})
        self.automata_count += 1
        self.add_automata(automata, 'Automata{}'.format(self.automata_count))

    def add_automata(self, automata, tab_name):
        new_tab = AutomataTab(text=tab_name)
        new_tab.automata = automata
        self.ids.automata_tabs.add_widget(new_tab)
        self.ids.automata_tabs.switch_to(new_tab)
        Clock.schedule_once(partial(new_tab.ids.tabs.switch_to, new_tab.ids.transition_tab))
        self.ids.btn_close.disabled = \
            self.ids.btn_save.disabled = \
            self.ids.btn_add_symbol.disabled = \
            self.ids.btn_add_state.disabled = \
            self.ids.btn_clear.disabled = False
        self.remake_table()

    def close_current(self):
        current = self.current_tab()
        tabs = self.ids.automata_tabs
        index = tabs.tab_list.index(current)
        tabs.remove_widget(current)
        if len(tabs.tab_list) > 0:
            tabs.switch_to(tabs.tab_list[index % len(tabs.tab_list)])
        else:
            tabs.clear_widgets()
            self.ids.btn_close.disabled = \
                self.ids.btn_save.disabled = \
                self.ids.btn_add_symbol.disabled = \
                self.ids.btn_add_state.disabled = \
                self.ids.btn_clear.disabled = True

    def clear(self):
        self.current_tab().automata = DFA.create(initial_state='q0',
                              transitions={},
                              final_states={})
        self.remake_table()
        self.dismiss_popup()

    def load_file(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, default_dir=self.default_dir)
        self._popup = Popup(title='Load', content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def save_file(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup, default_dir=self.default_dir)
        self._popup = Popup(title='Save', content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def add_symbol(self, symbol):
        self.dismiss_popup()

        self.current_tab().automata = with_symbol(self.current_automata(), symbol)
        automata = self.current_tab().automata
        pprint(dict(automata._asdict()))

        self.remake_table()

    def add_state(self):
        state = 'q{}'.format(len(self.current_automata().states) - 1)
        self.current_tab().automata = with_state(self.current_automata(), state)
        self.remake_table()

    def update_transition(self, transition, content, spinner):
        print('updating {} to {}'.format(transition, content.value))
        automata = self.current_automata()
        automata.transitions[transition] = content.value
        self.remake_table()
        self.dismiss_popup()

    def show_clear_popup(self):
        content = ConfirmDialog(yes=self.clear, no=self.dismiss_popup)
        self._popup = Popup(title='Do you really want to clear the automata?', content=content, size_hint=(None, None), size=(320, 92))
        self._popup.open()

    def show_input_dialog(self, title, action):
        content = InputDialog(pressed_ok=action)
        self._popup = Popup(title=title, content=content, size_hint=(None, None), size=(320, 92))
        self._popup.open()
        content.ids.input_box.focus = True

    def show_transition_edit_dialog(self, transition, title, action):
        content = TransitionEditDialog(pressed_ok=action)
        spinner = ShortSpinner(text='State', values=list({'-'} | self.current_automata().states), size_hint=(None, None), size=(48, 32))
        def update_content_value(sp_, text):
            print('new value: {} (old: {})'.format(text, content.value))
            content.value = text
        spinner.bind(text=update_content_value)
        content.ids.contents.add_widget(spinner)
        content.ids.contents.add_widget(Button(text='OK',
                                               size_hint=(None, None),
                                               size=(48, 32),
                                               on_release=partial(
                                                            self.update_transition,
                                                            transition,
                                                            content)))
        self._popup = Popup(title=title, content=content, size_hint=(None, None), size=(320, 92))
        self._popup.open()

    def dismiss_popup(self):
        try:
            self._popup.dismiss()
        except AttributeError as e:
            print('no popup to dismiss')

    def remake_table(self):
        transition_table = self.current_transition_table()
        transition_table.clear_widgets()

        header = TableRow()
        header.add_widget(TableHeader(text='q'))
        transition_table.add_widget(header)

        rows = {}
        automata = self.current_tab().automata
        if automata:
            for char in automata.alphabet:
                header.add_widget(TableHeader(text=char))
            for state in automata.states:
                if state is '-':
                    continue
                row = TableRow()
                rows[state] = [row]
                for char in automata.alphabet:
                    rows[state].append([])
                print(rows[state])
                state_name = state
                if state in automata.final_states:
                    state_name = '*' + state
                if state == automata.initial_state:
                    state_name = '→' + state
                row.add_widget(TableCell(text=state_name))

                for i, char in enumerate(automata.alphabet):
                    trans = automata.transitions[(state, char)]
                    if trans is not None:
                        rows[state][i + 1].append(trans)
                transition_table.add_widget(row)
            for j, state in enumerate(rows):
                row = rows[state][1:]
                for i, destiny in enumerate(row):
                    cell = TableCell(text='[-]')
                    if len(destiny) > 0:
                        cell.text = re.sub('\'', '', str(destiny))
                    cell.transition = (state, list(automata.alphabet)[i])
                    cell.on_touch_down = partial(self.edit_cell, cell, j, i)
                    rows[state][0].add_widget(cell)

        transition_table.width = len(transition_table.children[0].children) * 48
        transition_table.height = len(transition_table.children) * 48

    def edit_cell(self, cell, j, i, *args):
        if cell.collide_point(*args[0].pos) and args[0].is_double_tap:
            print('editint cell at {}'.format((j, i)))
            self.show_transition_edit_dialog(cell.transition, 'Edit transition {}'.format(cell.transition), self.update_transition)
