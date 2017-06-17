import itertools
import json
from itertools import chain, product
from typing import Dict, NamedTuple, Optional, Set, Tuple

Symbol = str
State = str


class DFA(NamedTuple):
    alphabet: Set[Symbol]
    states: Set[State]
    initial_state: State
    transitions: Dict[Tuple[Symbol, State], State]
    final_states: Set[State]

    def complete(self):
        transitions = self.transitions.copy()
        for state, symbol in itertools.product(self.states, self.alphabet):
            transitions.setdefault((state, symbol), 'qerr')

        if transitions != self.transitions:
            transitions.update({
                ('qerr', symbol): 'qerr' for symbol in self.alphabet
                })

        return DFA.create(
            initial_state=self.initial_state,
            transitions=transitions,
            final_states=self.final_states,
            )

    def __add__(self, other):
        return self.concatenate(other)

    def concatenate(self, other):
        return self.to_nfa().concatenate(other.to_nfa()).to_dfa()

    def __sub__(self, other):
        return self.difference(other)

    def difference(self, other):
        return self.complement().union(other).complement()

    def __invert__(self):
        return self.complement()

    def complement(self):
        complete = self.complete()
        return DFA.create(
            initial_state=complete.initial_state,
            transitions=complete.transitions,
            final_states=complete.states - complete.final_states,
            )

    def __and__(self, other):
        return self.intersect(other)

    def intersect(self, other):
        return self.complement().union(other.complement()).complement()

    def __or__(self, other):
        return self.union(other)

    def union(self, other):
        return self.to_nfa().union(other.to_nfa()).to_dfa()

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
        classes = [self.final_states, self.states - self.final_states]

        def equivalence_class(state) -> Set[State]:
            for klass in classes:
                if state in klass:
                    return klass

        def equivalents(this, klass):
            for that in klass:
                if all(equivalence_class(self.step(this, symbol)) ==
                               equivalence_class(self.step(that, symbol))
                       for symbol in self.alphabet):
                    yield that

        while True:
            new_classes = []

            for klass in (s.copy() for s in classes):
                first = next(q for q in klass)

                equiv_states = frozenset([first, *equivalents(first, klass)])
                new_classes.append(equiv_states)
                if equiv_states != klass:
                    new_classes.append(klass - equiv_states)

            if classes == new_classes:
                break

            classes = new_classes

        trans = {
            frozenset(state): f'q{i}' for i, state in enumerate(classes)
            }

        def is_final(klass):
            return any(state in self.final_states for state in klass)

        initial_state = next(c for c in classes if self.initial_state in c)
        return DFA.create(
            initial_state=trans[initial_state],
            transitions={
                (trans[equivalence_class(k[0])], k[1]):
                    trans[equivalence_class(v)]
                for k, v in self.transitions.items()
                },
            final_states={trans[c] for c in classes if is_final(c)},
            )

    def minimize(self):
        return self.remove_unreachable().merge_nondistinguishable().complete()

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
        from nfa import NFA  # fucking circular import
        return NFA.create(
            self.initial_state, {
                k: [v] for k, v in self.transitions.items()
                }, self.final_states
            )

    @classmethod
    def create(cls, initial_state, transitions, final_states):
        alphabet = {s for _, s in transitions}

        s = chain.from_iterable((k[0], v) for k, v in transitions.items())
        states = {initial_state} | set(final_states) | set(s)

        return cls(
            frozenset(alphabet),
            frozenset(states),
            initial_state,
            transitions,
            frozenset(final_states),
            )


def load_dfa(fp) -> DFA:
    raw = json.load(fp=fp)

    return DFA.create(
        initial_state=raw['initial_state'],
        transitions={(t[0], t[1]): t[2] for t in raw['transitions']},
        final_states=set(raw['final_states'])
        )


def dump_dfa(fp, dfa: DFA):
    json.dump(fp=fp, obj={
        'initial_state': dfa.initial_state,
        'transitions': [[k[0], k[1], v] for k, v in dfa.transitions.items()],
        'final_states': list(dfa.final_states),
        })
