from unittest import skip

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from orml import parser
from orml.tests.models import TestModel, TestModelChild


class TestORML(TestCase):
    def test_ints(self):
        a = parser.parse('1')
        self.assertEqual(a, 1)

    def test_floats(self):
        a = parser.parse('1.49')
        self.assertEqual(a, 1.49)

    def test_assignments(self):
        a = parser.parse([
            'a__in=5',
            'a__in'
        ])

    def test_lists(self):
        a = parser.parse('1,2,3')
        self.assertEqual(a, [1,2,3,])

    def test_dicts(self):
        d = parser.parse('a:1,b:2,c:3')
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        self.assertEqual(d['c'], 3)

    def test_dict_list(self):
        d = parser.parse('a:(1,2,3),b:(2,3,4),c:(3,4,5)')
        self.assertEqual(d['a'], [1,2,3])
        self.assertEqual(d['b'], [2,3,4])
        self.assertEqual(d['c'], [3,4,5])

    def test_sum_with_list(self):
        a = parser.parse('SUM(1,2,3)')
        self.assertEqual(6, a)

    def test_avg_with_list(self):
        a = parser.parse('AVG(0,5,10)')
        self.assertEqual(a, 5)

    def test_equals(self):
        self.assertTrue(parser.parse('5+5*5==30'))

    def test_blocks(self):
        a = parser.parse([
            'a=2',
            'a*15'
        ])
        self.assertEqual(a, 30)

    def test_model_resolution(self):
        model = parser.parse('tests.testmodel')
        self.assertEqual(TestModel, model)

    def test_querychain(self):
        a = parser.parse('id:3 | val:15, id:2 | id:1')

    def test_model_filtering(self):
        test_1 = TestModel.objects.create(
            t=TestModel.T1,
            val=15,
            note='Test 1'
        )
        test_2 = TestModel.objects.create(
            t=TestModel.T1,
            val=100,
            note='Test 2'
        )
        test_3 = TestModel.objects.create(
            t=TestModel.T2,
            val=1,
            note='Test 3'
        )

        test_3_child = TestModelChild.objects.create(
            parent=test_3,
            name="Test 3 Child"
        )

        query_1 = parser.parse('tests.testmodel{id:1}')
        self.assertEqual(test_1, query_1[0])

        query_2 = parser.parse('tests.testmodel{id:2}')
        self.assertEqual(test_2, query_2[0])

        query_3 = parser.parse('tests.testmodel{id:3}')
        self.assertEqual(test_3, query_3[0])

        query_4 = parser.parse('tests.testmodel{id__in:(1,3)}')
        self.assertEqual(len(query_4), 2)

        # Test accessor to value list on QuerySet
        query_5 = parser.parse('tests.testmodel{id__in:(1,3)}[id]')
        self.assertEqual(query_5, [1, 3])

        # Test multi accessor to dict[] on a QuerySet
        query_6 = parser.parse('tests.testmodel{id__in:(1,3)}[t, val, note]')
        self.assertEqual(query_6[0]['t'], test_1.t)
        self.assertEqual(query_6[0]['val'], test_1.val)
        self.assertEqual(query_6[0]['note'], test_1.note)

        self.assertEqual(query_6[1]['t'], test_3.t)
        self.assertEqual(query_6[1]['val'], test_3.val)
        self.assertEqual(query_6[1]['note'], test_3.note)

        # Nested queries and multiple statements
        query_7 = parser.parse('tests.testmodelchild{parent__in:(tests.testmodel{id__in:(1,3)}[id])}')
        query_8 = parser.parse([
            'parent_ids=tests.testmodel{id__in:(1,3)}[id]',
            'tests.testmodelchild{parent__in:parent_ids}'
        ])
        self.assertEqual(query_7[0], query_8[0])
