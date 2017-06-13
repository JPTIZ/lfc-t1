import copy
from collections import defaultdict
from itertools import chain
from typing import DefaultDict, FrozenSet, NamedTuple, Set, Tuple

Symbol = str
State = str
StateSet = FrozenSet[State]


class NFA(NamedTuple):
    EPSILON = '&'

    alphabet: Set[Symbol]
    states: Set[State]
    initial_state: State
    transitions: DefaultDict[Tuple[Symbol, State], Set[State]]
    final_states: Set[State]

    def __invert__(self):
        return self.complement()

    def complement(self):
        return NFA.create(
            initial_state=self.initial_state,
            transitions=self.transitions,
            final_states=self.states - self.final_states,
            )

    def __add__(self, other):
        return self.concatenate(other)

    def concatenate(self, other):
        def translate(mapping, trans):
            for k, v in mapping.items():
                yield (trans[k[0]], k[1]), frozenset(trans[s] for s in v)

        # sift up all states so we can chain the automatons together
        def offset(dfa, start):
            trans = {
                state: f'q{i}' for i, state in enumerate(dfa.states, start)
                }

            return NFA.create(
                trans[dfa.initial_state],
                dict(translate(dfa.transitions, trans)),
                frozenset(trans[s] for s in dfa.final_states),
                )

        other = offset(other, len(self.states))

        new_transitions = {
            (q, self.EPSILON): {other.initial_state} for q in self.final_states
            }

        new_transitions.update(self.transitions)
        new_transitions.update(other.transitions)

        return NFA.create(
            initial_state=self.initial_state,
            transitions=new_transitions,
            final_states=other.final_states,
            )

    def __or__(self, other):
        return self.union(other)

    def union(self, other):
        def translate(mapping, trans):
            for k, v in mapping.items():
                yield (trans[k[0]], k[1]), frozenset(trans[s] for s in v)

        # sift up all states so we can chain the automatons together
        def offset(dfa, start):
            trans = {
                state: f'q{i}' for i, state in enumerate(dfa.states, start)
                }

            return self.create(
                trans[dfa.initial_state],
                dict(translate(dfa.transitions, trans)),
                frozenset(trans[s] for s in dfa.final_states),
                )

        self_offset = offset(self, 1)
        other_offset = offset(other, len(self.states) + 1)

        new_transitions = {
            ('q0', self.EPSILON): {self_offset.initial_state,
                                   other_offset.initial_state}
            }

        new_transitions.update(self_offset.transitions)
        new_transitions.update(other_offset.transitions)

        return self.create(
            'q0',
            new_transitions,
            self_offset.final_states | other_offset.final_states)

    @classmethod
    def create(cls, initial_state, transitions, final_states):
        def freeze(t):
            for k, v in t.items():
                yield k, frozenset(v)

        new_transitions = defaultdict(frozenset, freeze(transitions))

        s = chain.from_iterable((k[0], *v) for k, v in new_transitions.items())
        states = {initial_state, } | final_states | set(s)

        return cls(
            frozenset({c for _, c in transitions if c != cls.EPSILON}),
            frozenset(states),
            initial_state,
            new_transitions,
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
        final_states = set()

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
            ), steps
