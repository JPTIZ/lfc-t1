import unittest
from dfa import DFA, load_dfa
from nfa import NFA


class DFATest(unittest.TestCase):
    def setUp(self):
        self.automaton = DFA(
            alphabet={'0', '1'},
            states={'q0', 'q1', 'q2', 'q3', 'q4', 'q5'},
            initial_state='q0',
            transitions={
                ('q0', '0'): 'q0',
                ('q0', '1'): 'q1',
                ('q1', '0'): 'q2',
                ('q1', '1'): 'q3',
                ('q2', '0'): 'q4',
                ('q2', '1'): 'q5',
                ('q3', '0'): 'q0',
                ('q3', '1'): 'q1',
                ('q4', '0'): 'q2',
                ('q4', '1'): 'q3',
                ('q5', '0'): 'q4',
                ('q5', '1'): 'q5',
                },
            final_states={'q1', 'q2', 'q3'},
            )

    def test_invert(self):
        automaton = DFA(
            alphabet={'0', '1'},
            states={'q0', 'q1'},
            initial_state='q0',
            transitions={
                ('q0', '1'): 'q1',
                },
            final_states={'q1'},
            )

        invert = ~automaton
        self.assertEqual({'q0'}, invert.final_states)

    def test_accept(self):
        self.assertFalse(self.automaton.accept('101'))
        self.assertTrue(self.automaton.accept('111'))

    def test_step(self):
        self.assertEqual(self.automaton.step('q0', '0'), 'q0')

    def test_remove_unreachable(self):
        automaton = DFA(
            alphabet={'0', '1'},
            states={'q0', 'q1', 'q2'},
            initial_state='q0',
            transitions={
                ('q0', '0'): 'q1',
                ('q2', '1'): 'q2',
                },
            final_states={'q1', 'q2'},
            )

        cleaned = automaton.remove_unreachable()
        self.assertSetEqual({'0'}, cleaned.alphabet)
        self.assertSetEqual({'q0', 'q1'}, cleaned.states)
        self.assertEqual('q0', cleaned.initial_state)
        self.assertDictEqual({
            ('q0', '0'): 'q1',
            }, cleaned.transitions)
        self.assertSetEqual({'q1'}, cleaned.final_states)

    def test_merge_nondistinguishable(self):
        # this automaton accepts 0*10* but it's bloated, taken from wikipedia
        automaton = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', '0'): 'q1',
                ('q0', '1'): 'q2',
                ('q1', '0'): 'q0',
                ('q1', '1'): 'q3',
                ('q2', '0'): 'q4',
                ('q2', '1'): 'q5',
                ('q3', '0'): 'q4',
                ('q3', '1'): 'q5',
                ('q4', '0'): 'q4',
                ('q4', '1'): 'q5',
                ('q5', '0'): 'q5',
                ('q5', '1'): 'q5',
                },
            final_states={'q2', 'q3', 'q4'},
            )

        cleaned = automaton.merge_nondistinguishable()
        self.assertSetEqual({'q0', 'q1', 'q2'}, cleaned.states)
        self.assertEqual(1, len(cleaned.final_states))
        initial = cleaned.initial_state
        final, *_ = cleaned.final_states
        other, *_ = cleaned.states - {initial, final}
        self.assertDictEqual({
            (initial, '0'): initial,
            (initial, '1'): final,
            (final, '0'): final,
            (final, '1'): other,
            (other, '0'): other,
            (other, '1'): other,
            }, cleaned.transitions)

    def test_load(self):
        with open('fixture.json') as fp:
            automaton = load_dfa(fp)

        self.assertSetEqual(self.automaton.alphabet, automaton.alphabet)
        self.assertSetEqual(self.automaton.states, automaton.states)
        self.assertEqual(self.automaton.initial_state, automaton.initial_state)
        self.assertDictEqual(self.automaton.transitions, automaton.transitions)
        self.assertSetEqual(self.automaton.final_states,
                            automaton.final_states)


class NFATest(unittest.TestCase):
    def setUp(self):
        self.automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q0'},
                ('q0', 'b'): {'q1'},
                ('q1', NFA.EPSILON): {'q0'},
                ('q1', 'a'): {'q2'},
                ('q2', 'a'): {'q3'},
                },
            final_states={'q3'},
            )

    def test_concatenate(self):
        automaton1 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q1'},
                ('q1', 'a'): {'q1'},
                },
            final_states={'q1'},
            )
        automaton2 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'b'): {'q1'},
                ('q1', 'b'): {'q1'},
                },
            final_states={'q1'},
            )

        concatenate = automaton1 + automaton2
        self.assertEqual({'a', 'b'}, concatenate.alphabet)
        self.assertSetEqual({'q0', 'q1', 'q2', 'q3'}, concatenate.states)
        self.assertSetEqual({'q3'}, concatenate.final_states)

        # too hard to test on epsilon-NFA
        cleaned = concatenate.remove_epsilon_transitions()
        final_a1 = cleaned.step(cleaned.initial_state, 'a')
        initial_a2 = cleaned.step(final_a1 'b')
        final, *_ = cleaned.final_states
        self.assertDictEqual({
            (cleaned.initial_state, 'a'): {final_a1},
            (final_a1, 'a'): {final_a1},
            (final_a1, 'b'): {initial_a2},
            (initial_a2, 'b'): {final},
            (final, 'b'): {final},
            }, cleaned.transitions)

    def test_union(self):
        automaton1 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q1'},
                ('q1', 'a'): {'q1'},
                },
            final_states={'q1'},
            )
        automaton2 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'b'): {'q1'},
                ('q1', 'b'): {'q1'},
                },
            final_states={'q1'},
            )

        union = automaton1 | automaton2
        self.assertSetEqual({'q0', 'q1', 'q2', 'q3', 'q4'}, union.states)
        self.assertEqual(2, len(union.final_states))

    def test_epsilon_closure(self):
        self.assertSetEqual({'q0', 'q1'}, self.automaton.epsilon_closure('q1'))

    def test_step(self):
        self.assertSetEqual({'q0', 'q1'}, self.automaton.step({'q0'}, 'b'))

    def test_to_dfa(self):
        # this automaton accepts a+
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q0', 'q1'},
                },
            final_states={'q1'},
            )

        dfa, *_ = automaton.to_dfa()
        self.assertSetEqual({'q0', 'q1'}, dfa.states)
        self.assertEqual(1, len(dfa.final_states))
        initial = dfa.initial_state
        final, *_ = dfa.final_states
        self.assertDictEqual({
            (initial, 'a'): final,
            (final, 'a'): final,
            }, dfa.transitions)

    def test_to_dfa_with_epsilon(self):
        # this automaton accepts a*b*
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q0'},
                ('q0', NFA.EPSILON): {'q1'},
                ('q1', 'b'): {'q1'},
                },
            final_states={'q1'},
            )

        dfa, *_ = automaton.to_dfa()
        self.assertSetEqual({'q0', 'q1'}, dfa.states)
        self.assertSetEqual({'q0', 'q1'}, dfa.final_states)
        initial = dfa.initial_state
        final, *_ = dfa.final_states - {initial, }
        other, *_ = dfa.states - {initial, }
        self.assertDictEqual({
            (initial, 'a'): initial,
            (initial, 'b'): final,
            (final, 'b'): final,
            }, dfa.transitions)

    def test_remove_epsilon_transitions(self):
        # taken from Ullman slides
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', '0'): {'q2'},
                ('q0', '1'): {'q1'},
                ('q1', '0'): {'q0'},
                ('q1', NFA.EPSILON): {'q2'},
                ('q2', '1'): {'q0'},
                ('q2', NFA.EPSILON): {'q1'},
                },
            final_states={'q2'},
            )

        cleaned = automaton.remove_epsilon_transitions()
        self.assertDictEqual({
            ('q0', '0'): {'q2'},
            ('q0', '1'): {'q1'},
            ('q1', '0'): {'q0'},
            ('q1', '1'): {'q0'},
            ('q2', '0'): {'q0'},
            ('q2', '1'): {'q0'},
            }, cleaned.transitions)
        self.assertSetEqual({'q1', 'q2'}, cleaned.final_states)


if __name__ == '__main__':
    unittest.main()
