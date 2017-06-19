import unittest

import io

from dfa import DFA, dump_dfa, load_dfa
from nfa import NFA, dump_nfa, load_nfa


class DFATest(unittest.TestCase):
    def assertIsomorphic(self, expected: DFA, value: DFA):
        self.assertSetEqual(set(), (expected - value).final_states)
        self.assertSetEqual(set(), (value - expected).final_states)

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

    def test_complete(self):
        automaton = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                },
            final_states={'q1'},
            )

        complete = automaton.complete()
        self.assertSetEqual({'q0', 'q1', 'qerr'}, complete.states)
        self.assertEqual('qerr', complete.transitions[('q1', 'a')])
        self.assertEqual('qerr', complete.transitions[('qerr', 'a')])

    def test_complement(self):
        automaton = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                },
            final_states={'q1'},
            )

        complement = ~automaton
        self.assertEqual('q0', complement.initial_state)
        self.assertDictEqual({
            ('q0', 'a'): 'q1',
            ('q1', 'a'): 'qerr',
            ('qerr', 'a'): 'qerr',
            }, complement.transitions)
        self.assertSetEqual({'q0', 'qerr'}, complement.final_states)

    def test_concatenate(self):
        automaton1 = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                },
            final_states={'q1'},
            )
        automaton2 = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'b'): 'q1',
                },
            final_states={'q1'},
            )

        expected = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                ('q1', 'b'): 'q2',
                },
            final_states={'q2'},
            )

        concatenate = automaton1 + automaton2
        self.assertTrue(concatenate.accept('ab'))
        self.assertFalse(concatenate.accept('aa'))
        self.assertFalse(concatenate.accept('bb'))
        self.assertIsomorphic(concatenate, expected)

    def test_difference(self):
        automaton1 = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q0',
                },
            final_states={'q0'},
            )
        automaton2 = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                },
            final_states={'q1'},
            )

        expected = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                ('q1', 'a'): 'q2',
                ('q2', 'a'): 'q2',
                },
            final_states={'q0', 'q2'},
            )

        difference = automaton1 - automaton2
        self.assertTrue(difference.accept(''))
        self.assertTrue(difference.accept('aa'))
        self.assertFalse(difference.accept('a'))
        self.assertIsomorphic(expected, difference)

    def test_union(self):
        automaton1 = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                },
            final_states={'q1'},
            )
        automaton2 = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'b'): 'q1',
                },
            final_states={'q1'},
            )

        expected = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                ('q0', 'b'): 'q1',
                },
            final_states={'q1'},
            )

        union = automaton1 | automaton2
        self.assertTrue(union.accept('a'))
        self.assertTrue(union.accept('b'))
        self.assertFalse(union.accept('aa'))
        self.assertFalse(union.accept('ab'))
        self.assertIsomorphic(expected, union)

    def test_accept(self):
        self.assertFalse(self.automaton.accept('101'))
        self.assertTrue(self.automaton.accept('111'))

    def test_rename(self):
        automaton = DFA.create(
            initial_state='q2',
            transitions={
                ('q2', 'a'): 'q1',
                ('q2', 'b'): 'q0',
                },
            final_states={'q0'},
            )

        renamed = automaton.rename()
        self.assertEqual('q0', renamed.initial_state)
        self.assertDictEqual({
            ('q0', 'a'): 'q1',
            ('q0', 'b'): 'q2',
            }, renamed.transitions)
        self.assertSetEqual({'q2'}, renamed.final_states)

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

    def test_to_nfa(self):
        automaton = DFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): 'q1',
                },
            final_states={'q1'},
            )

        nfa = automaton.to_nfa()
        self.assertEqual(automaton.initial_state, nfa.initial_state)
        self.assertDictEqual({
            ('q0', 'a'): {'q1'},
            }, nfa.transitions)
        self.assertSetEqual(automaton.final_states, nfa.final_states)

    def test_dump(self):
        automaton = DFA.create(
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

        out = io.StringIO()
        dump_dfa(out, automaton)
        out.seek(0)
        loaded = load_dfa(out)

        self.assertIsomorphic(automaton, loaded)

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
    def assertIsomorphic(self, expected: NFA, value: NFA):
        self.assertSetEqual(set(), (expected - value).final_states)
        self.assertSetEqual(set(), (value - expected).final_states)

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

    def test_complete(self):
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q1'},
                },
            final_states={'q1'},
            )

        complete = automaton.complete()
        self.assertSetEqual({'q0', 'q1', 'qerr'}, complete.states)
        self.assertSetEqual({'qerr'}, complete.transitions[('q1', 'a')])
        self.assertSetEqual({'qerr'}, complete.transitions[('qerr', 'a')])

        # should not add error state to complete automaton
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', NFA.EPSILON): {'q1'},
                },
            final_states={'q1'},
            )

        complete = automaton.complete()
        self.assertSetEqual({'q0', 'q1'}, complete.states)

    def test_complement(self):
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q1'},
                },
            final_states={'q1'},
            )

        complement = ~automaton
        self.assertEqual('q0', complement.initial_state)
        self.assertDictEqual({
            ('q0', 'a'): {'q1'},
            ('q1', 'a'): {'qerr'},
            ('qerr', 'a'): {'qerr'},
            }, complement.transitions)
        self.assertSetEqual({'q0', 'qerr'}, complement.final_states)

    def test_concatenate(self):
        automaton1 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q1'},
                },
            final_states={'q1'},
            )
        automaton2 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'b'): {'q1'},
                },
            final_states={'q1'},
            )

        concatenate = automaton1 + automaton2
        self.assertEqual('q0_0', concatenate.initial_state)
        self.assertDictEqual({
            ('q0_0', 'a'): {'q1_0'},
            ('q1_0', NFA.EPSILON): {'q0_1'},
            ('q0_1', 'b'): {'q1_1'},
            }, concatenate.transitions)
        self.assertSetEqual({'q1_1'}, concatenate.final_states)

    def test_union(self):
        automaton1 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q1'},
                },
            final_states={'q1'},
            )
        automaton2 = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'b'): {'q1'},
                },
            final_states={'q1'},
            )

        union = automaton1 | automaton2
        self.assertEqual('q0', union.initial_state)
        self.assertDictEqual({
            ('q0', NFA.EPSILON): {'q0_0', 'q0_1'},
            ('q0_0', 'a'): {'q1_0'},
            ('q0_1', 'b'): {'q1_1'},
            }, union.transitions)
        self.assertSetEqual({'q1_0', 'q1_1'}, union.final_states)

    def test_accept(self):
        self.assertFalse(self.automaton.accept('aba'))
        self.assertTrue(self.automaton.accept('abaa'))

    def test_epsilon_closure(self):
        self.assertSetEqual({'q0', 'q1'}, self.automaton.epsilon_closure('q1'))

    def test_step(self):
        self.assertSetEqual({'q0', 'q1'}, self.automaton.step({'q0'}, 'b'))

    def test_to_dfa(self):
        # this automaton accepts a+
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', 'a'): {'q1'},
                },
            final_states={'q1'},
            )

        dfa = automaton.to_dfa()
        initial = dfa.initial_state
        final, *_ = dfa.final_states
        self.assertDictEqual({
            (initial, 'a'): final,
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

        dfa = automaton.to_dfa()
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

        epsilon_free = automaton.remove_epsilon_transitions()
        self.assertEqual('q0', epsilon_free.initial_state)
        self.assertDictEqual({
            ('q0', '0'): {'q2'},
            ('q0', '1'): {'q1'},
            ('q1', '0'): {'q0'},
            ('q1', '1'): {'q0'},
            ('q2', '0'): {'q0'},
            ('q2', '1'): {'q0'},
            }, epsilon_free.transitions)
        self.assertSetEqual({'q1', 'q2'}, epsilon_free.final_states)

    def test_dump(self):
        automaton = NFA.create(
            initial_state='q0',
            transitions={
                ('q0', '0'): {'q0'},
                ('q0', '1'): {'q1'},
                ('q1', '0'): {'q2'},
                ('q1', '1'): {'q3'},
                ('q2', '0'): {'q4'},
                ('q2', '1'): {'q5'},
                ('q3', '0'): {'q0'},
                ('q3', '1'): {'q1'},
                ('q4', '0'): {'q2'},
                ('q4', '1'): {'q3'},
                ('q5', '0'): {'q4'},
                ('q5', '1'): {'q5'},
                },
            final_states={'q1', 'q2', 'q3'},
            )

        out = io.StringIO()
        dump_nfa(out, automaton)
        out.seek(0)
        loaded = load_nfa(out)

        self.assertIsomorphic(automaton, loaded)

    def test_load(self):
        with open('fixture.json') as fp:
            automaton = load_nfa(fp)

        self.assertSetEqual(self.automaton.alphabet, automaton.alphabet)
        self.assertSetEqual(self.automaton.states, automaton.states)
        self.assertEqual(self.automaton.initial_state,
                         automaton.initial_state)
        self.assertDictEqual(self.automaton.transitions,
                             automaton.transitions)
        self.assertSetEqual(self.automaton.final_states,
                            automaton.final_states)


if __name__ == '__main__':
    unittest.main()
