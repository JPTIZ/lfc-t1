import copy
import itertools
import json
from collections import defaultdict
from itertools import chain
from typing import DefaultDict, FrozenSet, NamedTuple, Tuple

import graphviz

Symbol = str
State = str
StateSet = FrozenSet[State]


def shrink(transitions):
    return {k: v for k, v in transitions.items() if v}


class NFA(NamedTuple):
    EPSILON = '&'

    alphabet: FrozenSet[Symbol]
    states: StateSet
    initial_state: State
    transitions: DefaultDict[Tuple[Symbol, State], StateSet]
    final_states: StateSet

    def __invert__(self):
        return self.complement()

    def complement(self):
        complete = self.complete()
        return NFA.create(
            initial_state=complete.initial_state,
            transitions=complete.transitions,
            final_states=complete.states - complete.final_states,
            )

    def __add__(self, other):
        return self.concatenate(other)

    def concatenate(self, other):
        new_transitions = {
            (f'{q}_0', self.EPSILON): {f'{other.initial_state}_1'}
            for q in self.final_states
            }

        new_transitions.update({
            (f'{src}_0', symbol): {f'{state}_0' for state in dst}
            for (src, symbol), dst in self.transitions.items()
            })

        new_transitions.update({
            (f'{src}_1', symbol): {f'{state}_1' for state in dst}
            for (src, symbol), dst in other.transitions.items()
            })

        return NFA.create(
            initial_state=f'{self.initial_state}_0',
            transitions=new_transitions,
            final_states={f'{state}_1' for state in other.final_states},
            )

    def __sub__(self, other):
        return self.difference(other)

    def difference(self, other):
        return self.complement().union(other).complement()

    def __or__(self, other):
        return self.union(other)

    def union(self, other):
        other = other.to_nfa()

        new_transitions = {
            ('q0', self.EPSILON): {f'{self.initial_state}_0',
                                   f'{other.initial_state}_1', }
            }

        new_transitions.update({
            (f'{src}_0', a): {f'{state}_0' for state in dst}
            for (src, a), dst in self.transitions.items()
            })

        new_transitions.update({
            (f'{src}_1', a): {f'{state}_1' for state in dst}
            for (src, a), dst in other.transitions.items()
            })

        return NFA.create(
            initial_state='q0',
            transitions=new_transitions,
            final_states={f'{state}_0' for state in self.final_states} |
                         {f'{state}_1' for state in other.final_states}
            )

    def complete(self):
        qerr = frozenset({'-'})

        transitions = copy.deepcopy(shrink(self.transitions))
        for (state, symbol) in itertools.product(self.states, self.alphabet):
            if (state, self.EPSILON) not in transitions:
                transitions.setdefault((state, symbol), qerr)

        if transitions != self.transitions:
            transitions.update({
                ('-', symbol): qerr for symbol in self.alphabet
                })

        return NFA.create(
            initial_state=self.initial_state,
            transitions=transitions,
            final_states=self.final_states,
            )

    @classmethod
    def create(cls, initial_state, transitions, final_states):
        transitions = defaultdict(frozenset, {
            k: frozenset(v) for k, v in transitions.items() if v
            })

        s = chain.from_iterable((k, *v) for (k, _), v in transitions.items())
        states = {initial_state, } | final_states | set(s)

        return cls(
            frozenset({c for _, c in transitions if c != cls.EPSILON}),
            frozenset(states),
            initial_state,
            transitions,
            frozenset(final_states),
            )

    def epsilon_closure(self, state: State) -> StateSet:
        closure, new_closure = {state, }, set()

        while closure != new_closure:
            new_closure = closure.copy()
            for state in new_closure:
                closure |= self.transitions[(state, self.EPSILON)]

        return frozenset(closure)

    def remove_epsilon_transitions(self):
        transitions = copy.deepcopy(self.transitions)
        final_states = set(self.final_states)

        __marker = object()

        for p in self.states:
            for q in self.epsilon_closure(p):
                for a in self.alphabet:
                    transitions[(p, a)] |= transitions[(q, a)]

                if q in self.final_states:
                    final_states.add(p)

            transitions.pop((p, self.EPSILON), __marker)

        return NFA.create(
            initial_state=self.initial_state,
            transitions=transitions,
            final_states=final_states,
            )

    def accept(self, word) -> bool:
        state = {self.initial_state}
        for symbol in word:
            state = self.step(state, symbol)
            if not state:
                return False
        return any(q in self.final_states for q in state)

    def step(self, states: StateSet, symbol: Symbol) -> StateSet:
        def reachable():
            for closure in chain(self.epsilon_closure(s) for s in states):
                for s in closure:
                    for t in self.transitions.get((s, symbol), set()):
                        for u in self.epsilon_closure(t):
                            yield u

        return frozenset(reachable())

    def to_dfa(self):
        from dfa import DFA  # fucking circular import

        cleaned = self.remove_epsilon_transitions()

        transitions = {}
        initial_state = frozenset({cleaned.initial_state, })
        states = {initial_state, }
        visited = set()

        def is_final(s):
            return any(q in cleaned.final_states for q in s)

        steps = []

        while states:
            state = states.pop()
            visited.add(state)

            for symbol in cleaned.alphabet:
                new_state = cleaned.step(state, symbol)
                if not new_state:
                    continue

                transitions[(state, symbol)] = new_state

                if new_state not in visited:
                    states.add(new_state)

            steps.append(DFA.create(
                initial_state=initial_state,
                transitions=transitions,
                final_states={state for state in visited if is_final(state)},
                ))

        trans = {
            state: f'q{i}' for i, state in zip(range(len(visited)), visited)
            }

        return DFA.create(
            initial_state=trans[initial_state],
            transitions={
                (trans[k[0]], k[1]): trans[v] for k, v in transitions.items()
                },
            final_states={trans[q] for q in visited if is_final(q)},
            )

    def to_nfa(self):
        return self

    def to_dot(self) -> graphviz.Digraph:  # pragma: no cover
        f = graphviz.Digraph(format='png')
        f.attr(rankdir='LR')

        f.attr('node', shape='none')
        f.node('qi')

        f.attr('node', shape='doublecircle')
        for state in self.final_states:
            f.node(state)

        f.attr('node', shape='circle')
        f.edge('qi', self.initial_state)
        for (src, symbol), dst in self.transitions.items():
            for q in dst:
                f.edge(src, q, label=symbol)

        return f


def load_nfa(fp) -> NFA:
    raw = json.load(fp=fp)

    return NFA.create(
        initial_state=raw['initial_state'],
        transitions={(t[0], t[1]): set(t[2]) for t in raw['transitions']},
        final_states=set(raw['final_states'])
        )


def dump_nfa(fp, nfa: NFA):
    json.dump(fp=fp, obj={
        'initial_state': nfa.initial_state,
        'transitions': [[k[0], k[1], list(v)]
                        for k, v in nfa.transitions.items()],
        'final_states': list(nfa.final_states),
        })
