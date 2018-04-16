import unittest
from copy import deepcopy

from jsgf import *
from jsgf.ext import Dictation


class Compilation(unittest.TestCase):
    def test_alt_set(self):
        e1 = AlternativeSet("a")
        e1.tag = "t"
        self.assertEqual(e1.compile(ignore_tags=True), "(a)")
        self.assertEqual(e1.compile(ignore_tags=False), "(a { t })")

        e2 = AlternativeSet("a b")
        e2.tag = "t"
        self.assertEqual(e2.compile(ignore_tags=True), "(a b)")
        self.assertEqual(e2.compile(ignore_tags=False), "(a b { t })")

        e3 = AlternativeSet("a", "b")
        e3.children[0].tag = "t1"
        e3.children[1].tag = "t2"
        self.assertEqual(e3.compile(ignore_tags=True), "(a|b)")
        self.assertEqual(e3.compile(ignore_tags=False), "(a { t1 }|b { t2 })")

    def test_kleene_star(self):
        e1 = KleeneStar("a")
        e1.tag = "t"
        self.assertEqual(e1.compile(ignore_tags=True), "(a)*")
        self.assertEqual(e1.compile(ignore_tags=False), "(a)* { t }")

        e2 = KleeneStar("a b")
        e2.tag = "t"
        self.assertEqual(e2.compile(ignore_tags=True), "(a b)*")
        self.assertEqual(e2.compile(ignore_tags=False), "(a b)* { t }")

        e3 = KleeneStar(Sequence("a", "b"))
        e3.tag = "t"
        self.assertEqual(e3.compile(ignore_tags=True), "(a b)*")
        self.assertEqual(e3.compile(ignore_tags=False), "(a b)* { t }")

    def test_literal(self):
        e1 = Literal("a")
        self.assertEqual(e1.compile(ignore_tags=True), "a")

        e2 = Literal("a b")
        self.assertEqual(e2.compile(ignore_tags=True), "a b")

        e3 = Literal("a b")
        e3.tag = "t"
        self.assertEqual(e3.compile(ignore_tags=False), "a b { t }")

    def test_optional_grouping(self):
        e1 = OptionalGrouping("a")
        self.assertEqual(e1.compile(ignore_tags=True), "[a]")

        e2 = OptionalGrouping("a b")
        e2.tag = "t"
        self.assertEqual(e2.compile(ignore_tags=True), "[a b]")
        self.assertEqual(e2.compile(ignore_tags=False), "[a b] { t }")

    def test_required_grouping(self):
        e1 = RequiredGrouping("a")
        e1.tag = "blah"
        self.assertEqual(e1.compile(ignore_tags=True), "(a)")
        self.assertEqual(e1.compile(ignore_tags=False), "(a { blah })")

        e2 = RequiredGrouping("a b")
        e2.tag = "t"
        self.assertEqual(e2.compile(ignore_tags=True), "(a b)")
        self.assertEqual(e2.compile(ignore_tags=False), "(a b { t })")

        e3 = RequiredGrouping("a", "b")
        e3.children[0].tag = "t1"
        e3.children[1].tag = "t2"
        self.assertEqual(e3.compile(ignore_tags=True), "(a b)")
        self.assertEqual(e3.compile(ignore_tags=False), "(a { t1 } b { t2 })")

    def test_repeat(self):
        e1 = Repeat("a")
        e1.tag = "t"
        self.assertEqual(e1.compile(ignore_tags=True), "(a)+")
        self.assertEqual(e1.compile(ignore_tags=False), "(a)+ { t }")

        e2 = Repeat("a b")
        e2.tag = "t"
        self.assertEqual(e2.compile(ignore_tags=True), "(a b)+")
        self.assertEqual(e2.compile(ignore_tags=False), "(a b)+ { t }")

        e3 = Repeat(Sequence("a", "b"))
        e3.tag = "t"
        self.assertEqual(e3.compile(ignore_tags=True), "(a b)+")
        self.assertEqual(e3.compile(ignore_tags=False), "(a b)+ { t }")

    def test_rule_ref(self):
        r = PublicRule("test", "a")
        rule_ref = RuleRef(r)
        rule_ref.tag = "ref"
        self.assertEqual(rule_ref.compile(ignore_tags=True), "<test>")
        self.assertEqual(rule_ref.compile(ignore_tags=False), "<test> { ref }")

    def test_sequence(self):
        e1 = Sequence("a")
        self.assertEqual(e1.compile(ignore_tags=True), "a")

        e2 = Sequence("a b")
        e2.tag = "t"
        self.assertEqual(e2.compile(ignore_tags=True), "a b")
        self.assertEqual(e2.compile(ignore_tags=False), "a b { t }")

        e3 = Sequence("a", "b")
        self.assertEqual(e3.compile(ignore_tags=True), "a b")

        e4 = Sequence("a", "b", "c")
        e4.children[1].tag = "t"
        self.assertEqual(e4.compile(ignore_tags=True), "a b c")
        self.assertEqual(e4.compile(ignore_tags=False), "a b { t } c")


class ParentCase(unittest.TestCase):
    def setUp(self):
        alt_set1 = AlternativeSet("hello", "hi", "hey")
        alt_set2 = AlternativeSet("alice", "bob", "eve")
        self.expansions = [Sequence(alt_set1, alt_set2), alt_set1, alt_set2]

    def test_parent_is_none(self):
        self.assertIsNone(self.expansions[0].parent)

    def check_descendants(self, expansion):
        for child in expansion.children:
            self.assertEqual(expansion, child.parent)
            self.check_descendants(child)

    def test_parent_is_set(self):
        # Recursively test the descendants of the Sequence expansion
        self.check_descendants(self.expansions[0])


class Comparisons(unittest.TestCase):
    def test_literals(self):
        self.assertEqual(Literal("hello"), Literal("hello"))
        self.assertNotEqual(Literal("hey"), Literal("hello"))
        self.assertNotEqual(Literal("hey"), Sequence(Literal("hello")))

    def test_alt_sets(self):
        self.assertEqual(AlternativeSet("hello", "hi"), AlternativeSet("hello", "hi"))
        self.assertNotEqual(AlternativeSet("hello", "hi"), AlternativeSet("hello"))
        self.assertNotEqual(AlternativeSet("hello", "hi"), AlternativeSet("hello"))
        self.assertNotEqual(AlternativeSet("hello", "hi"), Literal("hello"))

        # Test that child ordering doesn't matter
        self.assertEqual(AlternativeSet("hello", "hi"), AlternativeSet("hi", "hello"))

    def test_optional(self):
        self.assertEqual(OptionalGrouping("hello"), OptionalGrouping("hello"))
        self.assertNotEqual(OptionalGrouping("hello"), OptionalGrouping("hey"))
        self.assertNotEqual(OptionalGrouping("hello"), AlternativeSet("hello"))

    def test_required_grouping(self):
        self.assertEqual(RequiredGrouping("hello"), RequiredGrouping("hello"))
        self.assertNotEqual(RequiredGrouping("hello"), RequiredGrouping("hey"))
        self.assertNotEqual(RequiredGrouping("hello"), AlternativeSet("hello"))
        self.assertNotEqual(RequiredGrouping("hello"), AlternativeSet("hello"))

    def test_sequence(self):
        self.assertEqual(Sequence("hello"), Sequence("hello"))
        self.assertNotEqual(Sequence("hello"), Sequence("hey"))
        self.assertNotEqual(Sequence("hello"), AlternativeSet("hello"))
        self.assertNotEqual(Sequence("hello"), Literal("hello"))

    def test_repeat(self):
        self.assertEqual(Repeat("hello"), Repeat("hello"))
        self.assertNotEqual(Repeat("hello"), Repeat("hey"))
        self.assertNotEqual(Repeat("hello"), Literal("hello"))
        self.assertNotEqual(Repeat("hello"), Sequence(Literal("hello")))

    def test_kleene_star(self):
        self.assertEqual(KleeneStar("hello"), KleeneStar("hello"))
        self.assertNotEqual(KleeneStar("hello"), KleeneStar("hey"))
        self.assertNotEqual(KleeneStar("hello"), Literal("hello"))
        self.assertNotEqual(KleeneStar("hello"), Sequence(Literal("hello")))

    def test_rule_ref(self):
        rule1 = Rule("test", True, "test")
        rule2 = Rule("test", True, "testing")
        self.assertEqual(RuleRef(rule1), RuleRef(rule1))
        self.assertNotEqual(RuleRef(rule1), RuleRef(rule2))


class Copying(unittest.TestCase):
    def assert_copy_works(self, e):
        """Copy an expansion e and do some checks."""
        # Try first with deepcopy (default)
        e2 = e.copy()
        self.assertIsNot(e, e2)
        self.assertEqual(e, e2)

        # Then with shallow copying
        e3 = e.copy(shallow=True)
        self.assertIsNot(e, e3)
        self.assertEqual(e, e3)

        for c1, c2 in zip(e.children, e3.children):
            # Children of e and e3 should all be the same objects
            self.assertIs(c1, c2)

    def test_base(self):
        self.assert_copy_works(Expansion([]))

    def test_named_references(self):
        self.assert_copy_works(NamedRuleRef("test"))
        self.assert_copy_works(NullRef())
        self.assert_copy_works(VoidRef())

    def test_literals(self):
        self.assert_copy_works(Literal("test"))
        self.assert_copy_works(Dictation())

        # Check that regex patterns are not copied
        e1 = Literal("test")
        e2 = Dictation()

        # Initialise patterns - they are initialised lazily
        _ = e1.matching_regex_pattern
        _ = e2.matching_regex_pattern

        # Value of internal member '_pattern' should be None for copies
        self.assertIsNone(e1.copy()._pattern)
        self.assertIsNone(e2.copy()._pattern)

    def test_sequences(self):
        self.assert_copy_works(Sequence("test", "testing"))
        self.assert_copy_works(RequiredGrouping("test", "testing"))

    def test_alt_set(self):
        self.assert_copy_works(AlternativeSet("test", "testing"))

    def test_rule_ref(self):
        r1 = PublicRule("r1", "test")
        ref = RuleRef(r1)
        self.assert_copy_works(ref)

        # Check that a copy of a RuleRef references r1, not a copy of it.
        self.assertIs(ref.referenced_rule, ref.copy().referenced_rule)

        # Check that the same is true for a deep copied rule referencing r1
        self.assertIs(deepcopy(PublicRule("r2", ref)).expansion.referenced_rule, r1)

    def test_repeat(self):
        self.assert_copy_works(Repeat("testing"))
        self.assert_copy_works(KleeneStar("testing"))


class AncestorProperties(unittest.TestCase):
    """
    Test the ancestor properties of the Expansion class and its subclasses.
    """
    def test_is_optional(self):
        e1 = OptionalGrouping("hello")
        self.assertTrue(e1.is_optional)

        e2 = Literal("hello")
        self.assertFalse(e2.is_optional)

        e3 = Sequence(Literal("hello"))
        self.assertFalse(e3.is_optional)

        e4 = Sequence(Literal("hello"), OptionalGrouping("there"))
        self.assertFalse(e4.is_optional)
        self.assertTrue(e4.children[1].is_optional)
        self.assertTrue(e4.children[1].child.is_optional)

        e5 = Sequence(
            "a", OptionalGrouping("b"),
            Sequence("c", OptionalGrouping("d"))
        )

        a = e5.children[0]
        opt1 = e5.children[1]
        b = opt1.child
        seq2 = e5.children[2]
        c = seq2.children[0]
        opt2 = seq2.children[1]
        d = opt2.child
        self.assertFalse(e5.is_optional)
        self.assertFalse(a.is_optional)
        self.assertTrue(opt1.is_optional)
        self.assertTrue(opt2.is_optional)
        self.assertTrue(b.is_optional)
        self.assertTrue(opt2.is_optional)
        self.assertTrue(d.is_optional)
        self.assertFalse(c.is_optional)

    def test_is_alternative(self):
        e1 = AlternativeSet("hello")
        self.assertTrue(e1.is_alternative)

        e2 = Literal("hello")
        self.assertFalse(e2.is_alternative)

        e3 = Sequence(Literal("hello"))
        self.assertFalse(e3.is_alternative)

        e4 = AlternativeSet(Literal("hello"), Literal("hi"), Literal("hey"))
        for child in e4.children:
            self.assertTrue(child.is_alternative)

        e5 = Sequence(e4)
        self.assertFalse(e5.is_alternative)

        e6 = AlternativeSet(Literal("hello"), AlternativeSet("hi there",
                                                             "hello there"),
                            Literal("hey"))
        for leaf in e6.leaves:
            self.assertTrue(leaf.is_alternative)

    def test_is_descendant_of(self):
        e1 = Sequence("hello")
        self.assertTrue(e1.children[0].is_descendant_of(e1))
        self.assertFalse(e1.is_descendant_of(e1))
        self.assertFalse(e1.is_descendant_of(e1.children[0]))

        r = Rule("n", False, AlternativeSet("one", "two", "three"))
        e2 = RuleRef(r)
        self.assertFalse(e2.is_descendant_of(e2))

        # Expansions part of the 'n' rule are descendants of e2
        def assert_descendant(x):
            self.assertTrue(x.is_descendant_of(e2))

        map_expansion(r.expansion, assert_descendant)


class LiteralRepetitionAncestor(unittest.TestCase):
    def setUp(self):
        self.seq = Sequence("hello", "world")

    def test_no_repetition(self):
        self.assertIsNone(Literal("hello").repetition_ancestor)
        self.assertFalse(self.seq.children[0].repetition_ancestor)
        self.assertFalse(self.seq.children[1].repetition_ancestor)

    def test_with_repeat(self):
        rep1 = Repeat("hello")
        rep2 = Repeat(self.seq)
        self.assertEqual(rep1.child.repetition_ancestor, rep1)
        self.assertEqual(rep2.child.children[0].repetition_ancestor, rep2)

    def test_with_kleene_star(self):
        k1 = KleeneStar("hello")
        k2 = KleeneStar(self.seq)
        self.assertEqual(k1.child.repetition_ancestor, k1)
        self.assertEqual(k2.child.children[1].repetition_ancestor, k2)


class MutuallyExclusiveOfCase(unittest.TestCase):
    def test_no_alternative_sets(self):
        e1 = Literal("hi")
        e2 = Literal("hello")
        self.assertFalse(e1.mutually_exclusive_of(e2))

    def test_one_alternative_set(self):
        e1 = AlternativeSet("hi", "hello")
        self.assertTrue(e1.children[0].mutually_exclusive_of(e1.children[1]))

        e2 = AlternativeSet(Sequence("hi", "there"), "hello")
        self.assertTrue(e2.children[0]
                        .mutually_exclusive_of(e2.children[1]))
        self.assertTrue(e2.children[0].children[0]
                        .mutually_exclusive_of(e2.children[1]))
        self.assertTrue(e2.children[0].children[1]
                        .mutually_exclusive_of(e2.children[1]))

    def test_two_alternative_sets(self):
        e1 = Sequence(AlternativeSet(Sequence("a", "b"), "c"),
                      AlternativeSet("d", "e"))
        as1, as2 = e1.children[0], e1.children[1]
        seq2 = as1.children[0]
        a, b, c = seq2.children[0], seq2.children[1], as1.children[1]
        d, e = as2.children[0], as2.children[1]

        self.assertFalse(as1.mutually_exclusive_of(as2))
        self.assertTrue(a.mutually_exclusive_of(c))
        self.assertTrue(b.mutually_exclusive_of(c))
        self.assertFalse(a.mutually_exclusive_of(b))

        self.assertEqual(d.mutually_exclusive_of(e), e.mutually_exclusive_of(d),
                         "mutual_exclusive_of should be a commutative operation "
                         "(order does not matter)")
        self.assertTrue(d.mutually_exclusive_of(e))
        self.assertFalse(a.mutually_exclusive_of(d))
        self.assertFalse(a.mutually_exclusive_of(e))


class ExpansionTreeConstructs(unittest.TestCase):
    """
    Tests for functions and classes that operate on expansion trees, such as
    map_expansion, flat_map_expansion, filter_expansion and JointTreeContext.
    """
    def setUp(self):
        self.map_to_string = lambda x: "%s" % x
        self.map_to_current_match = lambda x: x.current_match
        self.find_letter = lambda x, l: hasattr(x, "text") and x.text == l
        self.find_a = lambda x: self.find_letter(x, "a")
        self.find_b = lambda x: self.find_letter(x, "b")
        self.find_seq = lambda x: isinstance(x, Sequence)

    def test_default_arguments(self):
        e = Sequence("hello")
        self.assertEqual(map_expansion(e), (
            e, ((Literal("hello"), ()),)
        ))
        self.assertEqual(flat_map_expansion(e), [e, Literal("hello")])
        self.assertEqual(filter_expansion(e), [e, Literal("hello")])

    def test_base_map(self):
        e = Literal("hello")
        mapped1 = map_expansion(e, self.map_to_string, TraversalOrder.PreOrder)
        self.assertEqual(mapped1[0], "%s" % e)

        mapped2 = map_expansion(e, self.map_to_string, TraversalOrder.PostOrder)
        self.assertEqual(mapped2[1], "%s" % e)

    def test_simple_map(self):
        e = Sequence("hello", "world")
        mapped1 = map_expansion(e, self.map_to_string, TraversalOrder.PreOrder)
        self.assertEqual(mapped1, (
            "Sequence(Literal('hello'), Literal('world'))", (
                ("Literal('hello')", ()),
                ("Literal('world')", ())
            )))

        mapped2 = map_expansion(e, self.map_to_string, TraversalOrder.PostOrder)
        self.assertEqual(mapped2, (
            (((), "Literal('hello')"), ((), "Literal('world')")),
            "Sequence(Literal('hello'), Literal('world'))"
        ))

    def test_using_rule_ref(self):
        """
        Test map_expansion using a RuleRef.
        """
        r = HiddenRule("name", AlternativeSet("alice", "bob"))
        e = RuleRef(r)
        self.assertEqual(map_expansion(e), (
            RuleRef(r), (
                (AlternativeSet("alice", "bob"), (
                    (Literal("alice"), ()),
                    (Literal("bob"), ())
                ))
            )
        ))

    def test_map_with_matches(self):
        e = Sequence("hello", "world")
        e.matches("hello world")  # assuming matches tests pass
        mapped = map_expansion(e, self.map_to_current_match)
        self.assertEqual(mapped, (
            "hello world", (
                ("hello", ()),
                ("world", ())
            )))

    def test_filter_base(self):
        e = Literal("hello")
        self.assertEqual(
            filter_expansion(e, lambda x: x.text == "hello",
                             TraversalOrder.PreOrder),
            [Literal("hello")])

        self.assertEqual(
            filter_expansion(e, lambda x: x.text == "hello",
                             TraversalOrder.PostOrder),
            [Literal("hello")])

    def test_filter_simple(self):
        e = Sequence("a", "b", "c")
        literals = e.children
        self.assertEqual(
            filter_expansion(e, lambda x: isinstance(x, Literal),
                             TraversalOrder.PreOrder),
            literals)

        self.assertEqual(
            filter_expansion(e, lambda x: isinstance(x, Literal),
                             TraversalOrder.PostOrder),
            literals)

    def test_filter_with_matches(self):
        e1 = Sequence("a", "b", "c")
        a, b, c = e1.children
        e1.matches("a b c")
        self.assertEqual(
            filter_expansion(e1, lambda x: x.current_match is not None,
                             TraversalOrder.PreOrder),
            [e1, a, b, c])

        self.assertEqual(
            filter_expansion(e1, lambda x: x.current_match is not None,
                             TraversalOrder.PostOrder),
            [a, b, c, e1])

        e2 = Sequence("d", OptionalGrouping("e"), "f")
        d, opt, f = e2.children
        e = opt.child
        e2.matches("d f")
        self.assertEqual(
            filter_expansion(e2, lambda x: x.current_match is not None,
                             TraversalOrder.PreOrder),
            [e2, d, opt, e, f])

        self.assertEqual(
            filter_expansion(e2, lambda x: x.current_match is not None,
                             TraversalOrder.PostOrder),
            [d, e, opt, f, e2])

    def test_flat_map_base(self):
        e = Literal("hello")
        self.assertEqual(
            flat_map_expansion(e, order=TraversalOrder.PreOrder),
            [e])

        self.assertEqual(
            flat_map_expansion(e, order=TraversalOrder.PostOrder),
            [e])

    def test_flat_map_simple(self):
        e = Sequence("a", AlternativeSet("b", "c"), "d")
        a, alt_set, d = e.children
        b, c = alt_set.children
        self.assertEqual(
            flat_map_expansion(e, order=TraversalOrder.PreOrder),
            [e, a, alt_set, b, c, d])

        self.assertEqual(
            flat_map_expansion(e, order=TraversalOrder.PostOrder),
            [a, b, c, alt_set, d, e])

    def test_joint_tree_context(self):
        """JointTreeContext joins and detaches trees correctly"""
        r1 = PublicRule("r1", "hi")
        ref = RuleRef(r1)
        e = AlternativeSet(ref, "hello")
        self.assertIsNone(r1.expansion.parent)
        self.assertFalse(r1.expansion.mutually_exclusive_of(e.children[1]),
                         "'hi' shouldn't be mutually exclusive of 'hello' "
                         "alternative yet")
        with JointTreeContext(e):
            self.assertEqual(r1.expansion.parent, ref,
                             "parent of r1.expansion changes to ref")
            self.assertTrue(r1.expansion.mutually_exclusive_of(e.children[1]),
                            "'hi' should be mutually exclusive of 'hello' within a "
                            "JointTreeContext")
        self.assertIsNone(r1.expansion.parent)
        self.assertFalse(r1.expansion.mutually_exclusive_of(e.children[1]))

    def test_find_expansion(self):
        e = Sequence("a", "a", "b")
        self.assertIs(find_expansion(e, self.find_a, TraversalOrder.PreOrder),
                      e.children[0])
        self.assertIs(find_expansion(e, self.find_a, TraversalOrder.PostOrder),
                      e.children[0])
        self.assertIs(find_expansion(e, self.find_b, TraversalOrder.PreOrder),
                      e.children[2])
        self.assertIs(find_expansion(e, self.find_b, TraversalOrder.PostOrder),
                      e.children[2])

    def test_find_expansion_rule_ref(self):
        """find_expansion correctly traverses through referenced rules"""
        r = Rule("n", False, AlternativeSet("a", "b", "c"))
        e1 = RuleRef(r)
        e2 = OptionalGrouping(RuleRef(r))
        self.assertIs(find_expansion(e1, self.find_a, TraversalOrder.PreOrder),
                      r.expansion.children[0])
        self.assertIs(find_expansion(e1, self.find_a, TraversalOrder.PreOrder),
                      r.expansion.children[0])
        self.assertIs(find_expansion(e2, self.find_b, TraversalOrder.PreOrder),
                      r.expansion.children[1])
        self.assertIs(find_expansion(e2, self.find_b, TraversalOrder.PreOrder),
                      r.expansion.children[1])

    def test_find_expansion_order(self):
        inner_seq = Sequence("a", "b")
        e = Sequence(AlternativeSet(inner_seq, "c"))
        self.assertIs(find_expansion(e, self.find_seq, TraversalOrder.PreOrder), e)
        self.assertIs(find_expansion(e, self.find_seq, TraversalOrder.PostOrder),
                      inner_seq)

    def test_find_expansion_optimisation(self):
        """find_expansion only searches until a match is found"""
        visited = []
        e = Sequence("a", "a", "b")

        def find_a(x):
            visited.append(x)
            return self.find_a(x)

        self.assertIs(find_expansion(e, find_a, TraversalOrder.PreOrder),
                      e.children[0])
        self.assertListEqual(visited, [e, e.children[0]])

        # Reset the visited list and test with a post order traversal
        visited = []
        self.assertIs(find_expansion(e, find_a, TraversalOrder.PostOrder),
                      e.children[0])
        self.assertListEqual(visited, [e.children[0]])

        # Test again finding 'b' instead
        visited = []

        def find_b(x):
            visited.append(x)
            return self.find_b(x)

        self.assertIs(find_expansion(e, find_b, TraversalOrder.PreOrder),
                      e.children[2])
        self.assertListEqual(visited, [e] + e.children)

        # Reset the visited list and test with a post order traversal
        visited = []
        self.assertIs(find_expansion(e, find_b, TraversalOrder.PostOrder),
                      e.children[2])
        self.assertListEqual(visited, e.children)


class LeavesProperty(unittest.TestCase):
    """
    Test the leaves property of the Expansion classes.
    """
    def test_base(self):
        e = Literal("hello")
        self.assertListEqual(e.leaves, [Literal("hello")])

    def test_new_leaf_type(self):
        class TestLeaf(Expansion):
            def __init__(self):
                super(TestLeaf, self).__init__([])

        e = TestLeaf()
        self.assertListEqual(e.leaves, [TestLeaf()])

    def test_multiple(self):
        e = Sequence(Literal("hello"), AlternativeSet("there", "friend"))
        self.assertListEqual(e.leaves, [Literal("hello"), Literal("there"),
                                        Literal("friend")],
                             "leaves should be in sequence from left to right.")

    def test_with_rule_ref(self):
        r = PublicRule("test", Literal("hi"))
        e = RuleRef(r)
        self.assertListEqual(e.leaves, [Literal("hi")])


class LeavesAfterLiteralProperty(unittest.TestCase):
    def test_base(self):
        e = Literal("a")
        self.assertListEqual(list(e.leaves_after), [])

    def test_multiple(self):
        e = Sequence("a", "b")
        self.assertListEqual(list(e.children[0].leaves_after), [e.children[1]])
        self.assertListEqual(list(e.children[1].leaves_after), [])

    def test_complex(self):
        x = Sequence(
            AlternativeSet(Sequence("a", "b"), Sequence("c", "d")),
            "e", OptionalGrouping("f")
        )
        a = x.children[0].children[0].children[0]
        b = x.children[0].children[0].children[1]
        c = x.children[0].children[1].children[0]
        d = x.children[0].children[1].children[1]
        e = x.children[1]
        f = x.children[2].child

        self.assertListEqual(list(a.leaves_after), [b, c, d, e, f])
        self.assertListEqual(list(b.leaves_after), [c, d, e, f])
        self.assertListEqual(list(c.leaves_after), [d, e, f])
        self.assertListEqual(list(d.leaves_after), [e, f])
        self.assertListEqual(list(e.leaves_after), [f])
        self.assertListEqual(list(f.leaves_after), [])


class RootExpansionProperty(unittest.TestCase):
    def test_base(self):
        e = Literal("hello")
        self.assertEqual(e.root_expansion, e)

    def test_multiple(self):
        e = Sequence(Literal("hello"), AlternativeSet("there", "friend"))
        hello = e.children[0]
        alt_set = e.children[1]
        there = e.children[1].children[0]
        friend = e.children[1].children[1]
        self.assertEqual(e.root_expansion, e)
        self.assertEqual(alt_set.root_expansion, e)
        self.assertEqual(hello.root_expansion, e)
        self.assertEqual(there.root_expansion, e)
        self.assertEqual(friend.root_expansion, e)


if __name__ == '__main__':
    unittest.main()
