from collections import defaultdict
from itertools import chain
from typing import DefaultDict, FrozenSet, List, NamedTuple, Tuple

Symbol = str
State = str


class NFA(NamedTuple):
    EPSILON = '&'

    alphabet: FrozenSet[Symbol]
    states: FrozenSet[State]
    initial_state: State
    transitions: DefaultDict[Tuple[Symbol, State], FrozenSet[State]]
    final_states: FrozenSet[State]

    @classmethod
    def create(cls, initial_state, transitions, final_states):
        new_transitions = defaultdict(frozenset, {
            k: frozenset(v) for k, v in transitions.items()
            })

        s = chain.from_iterable((k[0], v) for k, v in new_transitions.items())
        states = {initial_state, } | frozenset(final_states) | set(s)

        return cls(
            frozenset(c for _, c in transitions),
            frozenset(states),
            initial_state,
            new_transitions,
            frozenset(final_states),
            )

    def epsilon_closure(self, state: State) -> FrozenSet[State]:
        closure, new_closure = frozenset({state, }), frozenset()

        while closure != new_closure:
            new_closure = closure.copy()
            for state in closure:
                closure |= self.transitions[(state, self.EPSILON)]

        return closure

    def step(self, states: FrozenSet[State], symbol: Symbol) -> FrozenSet[
        State]:
        def reachable():
            for s in states:
                for t in self.transitions.get((s, symbol)):
                    for u in self.epsilon_closure(t):
                        yield u

        return frozenset(reachable())

    def to_dfa(self):
        pass
        # raise NotImplementedError
