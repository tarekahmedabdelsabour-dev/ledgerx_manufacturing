import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from ledgerx_manufacturing.engine import logic as L


class TestLogic(unittest.TestCase):
	def test_clean(self):
		self.assertEqual(L.clean_code(" JC-0001\r\n"), "JC-0001")
		self.assertEqual(L.clean_code(None), "")

	def test_split_qty(self):
		self.assertEqual(L.split_qty("ITEM-1*12"), ("ITEM-1", 12.0))
		self.assertEqual(L.split_qty("ITEM-1"), ("ITEM-1", 1.0))
		self.assertEqual(L.split_qty("A*B*3"), ("A*B", 3.0))
		self.assertEqual(L.split_qty("ITEM*0"), ("ITEM*0", 1.0))
		self.assertEqual(L.split_qty("*5"), ("*5", 1.0))

	def test_cycle_split(self):
		self.assertEqual(L.cycle_split(100, 0, 0, 40, 5), (55.0, 100.0))
		self.assertEqual(L.cycle_split(100, 60, 5, 35, 0), (0.0, 35.0))
		with self.assertRaises(ValueError):
			L.cycle_split(100, 90, 0, 10, 5)
		with self.assertRaises(ValueError):
			L.cycle_split(100, 0, 0, -1, 0)

	def test_scrap(self):
		self.assertEqual(L.scrap_pct(95, 5), 5.0)
		self.assertEqual(L.scrap_pct(0, 0), 0.0)

	def test_efficiency(self):
		self.assertEqual(L.efficiency(120, 2, 50), (60.0, 120.0))
		self.assertEqual(L.efficiency(10, 0, 50), (0.0, 0.0))
		self.assertEqual(L.efficiency(10, 2, 0), (5.0, 0.0))

	def test_cost(self):
		self.assertEqual(L.unit_cost(800, 200, 100), 10.0)
		self.assertEqual(L.unit_cost(1, 1, 0), 0.0)
		self.assertEqual(L.cost_variance(11, 10), (1.0, 10.0))
		self.assertEqual(L.cost_variance(9, 0), (9.0, 0.0))

	def test_issue(self):
		self.assertEqual(L.outstanding(10, 4), 6.0)
		self.assertEqual(L.outstanding(10, 12), 0.0)
		self.assertTrue(L.issue_limit(10, 9, 1))
		self.assertFalse(L.issue_limit(10, 9, 2))
		self.assertTrue(L.issue_limit(10, 10, 1, 10))

	def test_buttons(self):
		self.assertEqual(L.next_status(False, False, 5), ["start"])
		self.assertEqual(L.next_status(False, True, 5), ["pause", "finish"])
		self.assertEqual(L.next_status(True, False, 5), ["resume", "finish"])
		self.assertEqual(L.next_status(False, False, 0), [])


if __name__ == "__main__":
	unittest.main()
