from collections import defaultdict
from itertools import chain
from typing import DefaultDict, NamedTuple, Set, Tuple

Symbol = str
State = str


class NFA(NamedTuple):
    EPSILON = '&'

    alphabet: Set[Symbol]
    states: Set[State]
    initial_state: State
    transitions: DefaultDict[Tuple[Symbol, State], Set[State]]
    final_states: Set[State]

    @classmethod
    def create(cls, initial_state, transitions, final_states):
        new_transitions = defaultdict(set, transitions)

        s = chain.from_iterable((k[0], *v) for k, v in new_transitions.items())
        states = {initial_state, } | final_states | set(s)

        return cls(
            {c for _, c in transitions},
            states,
            initial_state,
            new_transitions,
            final_states,
            )

    def epsilon_closure(self, state: State) -> Set[State]:
        closure, new_closure = {state, }, set()

        while closure != new_closure:
            new_closure = closure.copy()
            for state in new_closure:
                closure |= self.transitions[(state, self.EPSILON)]

        return closure

    def step(self, states: Set[State], symbol: Symbol) -> Set[State]:
        def reachable():
            for s in states:
                for t in self.transitions.get((s, symbol), set()):
                    for u in self.epsilon_closure(t):
                        yield u

        return frozenset(reachable())

    def to_dfa(self):
        transitions = {}
        initial_state = frozenset({self.initial_state, })
        states = {initial_state, }
        visited = set()

        while states:
            state = states.pop()
            visited.add(state)

            for symbol in self.alphabet:
                new_state = self.step(state, symbol)
                transitions[(state, symbol)] = new_state

                if new_state not in visited:
                    states.add(new_state)

        trans = {
            state: f'q{i}' for i, state in zip(range(len(visited)), visited)
            }

        from dfa import DFA  # fucking circular import
        return DFA.create(
            initial_state=trans[initial_state],
            transitions={
                (trans[k[0]], k[1]): trans[v] for k, v in transitions.items()
                },
            final_states={
                trans[state] for state in visited
                if any(q in self.final_states for q in state)
                }
            )
