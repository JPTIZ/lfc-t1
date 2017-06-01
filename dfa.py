import json
from itertools import chain, product
from typing import Dict, FrozenSet, NamedTuple, Optional, Tuple

Symbol = str
State = str


class DFA(NamedTuple):
    alphabet: FrozenSet[Symbol]
    states: FrozenSet[State]
    initial_state: State
    transitions: Dict[Tuple[Symbol, State], State]
    final_states: FrozenSet[State]

    def copy(self):
        return DFA(
            alphabet=self.alphabet.copy(),
            states=self.states.copy(),
            initial_state=self.initial_state.copy(),
            transitions=self.transitions.copy(),
            final_states=self.final_states.copy(),
            )

    def remove_unreachable(self):
        reachable = {self.initial_state, }
        states = {self.initial_state, }

        def reachable_from(states):
            for key in product(states, self.alphabet):
                if key in self.transitions:
                    yield self.transitions[key]

        while states:
            states = {state for state in reachable_from(states)} - reachable
            reachable |= states

        return self.create(
            initial_state=self.initial_state,
            transitions={
                k: v for k, v in self.transitions.items()
                if k[0] in reachable and v in reachable
                },
            final_states={q for q in self.final_states if q in reachable}
            )

    def merge_nondistinguishable(self):
        p = {self.final_states, self.states - self.final_states}
        w = {self.final_states, }

        print(p)

        while len(w) > 0:
            a = w.pop()

            for c in self.alphabet:
                x = frozenset(k[0] for k, v in self.transitions.items()
                              if k[1] == c and v in a)

                for y in p.copy():
                    intersection, difference = x & y, y - x
                    if not intersection or not difference:
                        continue

                    p.remove(y)
                    p.add(intersection)
                    p.add(difference)

                    if y in w:
                        w.remove(y)
                        w.add(intersection)
                        w.add(difference)
                    else:
                        w.add(intersection if len(intersection) <= len(
                            difference) else difference)

            print(p)

        return self.create(
            initial_state=next(q for q in p if self.initial_state in q),
            transitions={},
            final_states={q for q in p
                          if any(qf in q for qf in self.final_states)}
            )

    def accept(self, word) -> bool:
        state = self.initial_state
        for symbol in word:
            state = self.step(state, symbol)
            if not state:
                return False
        return state in self.final_states

    def step(self, state: State, symbol: Symbol) -> Optional[str]:
        return self.transitions.get((state, symbol))

    def to_nfa(self):
        return NFA.create(
            self.initial_state, {
                k: [v] for k, v in self.transitions.items()
                }, self.final_states
            )

    @classmethod
    def create(cls, initial_state, transitions, final_states):
        alphabet = {s for _, s in transitions}

        s = chain.from_iterable((k[0], v) for k, v in transitions.items())
        states = {initial_state, } | set(final_states) | set(s)

        return cls(
            frozenset(alphabet),
            frozenset(states),
            initial_state,
            transitions,
            frozenset(final_states),
            )


def load_dfa(fp) -> DFA:
    raw = json.load(fp)

    return DFA.create(
        initial_state=raw['initial_state'],
        transitions={(t[0], t[1]): t[2] for t in raw['transitions']},
        final_states=set(raw['final_states'])
        )
