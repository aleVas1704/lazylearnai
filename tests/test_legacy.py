import unittest

from backend.modules.guided_math import rules

EX = {"a_num": 3, "a_den": 4, "operator": "+", "b_num": 1, "b_den": 6}


class LegacyRegression(unittest.TestCase):
    def test_ten_exercises_and_four_stages(self):
        self.assertEqual(len(rules.validate_exercises([EX] * 10)), 10)
        for index in range(1, 11):
            stage = "concept"
            for message, expected in [
                ("MCM", "mcm"),
                ("12", "equivalents"),
                ("9/12 y 2/12", "result"),
                ("11/12", "done"),
            ]:
                _, stage, finished = rules.next_step(EX, index, stage, message)
                self.assertEqual(stage, expected)
            self.assertTrue(finished)

    def test_wrong_answers_do_not_advance(self):
        for stage in rules.STAGES[:-1]:
            for message in ("No entiendo", "Dame la respuesta", "18"):
                self.assertEqual(rules.next_step(EX, 1, stage, message)[1], stage)
        self.assertEqual(rules.next_step(EX, 1, "concept", "12")[1], "concept")
        self.assertEqual(rules.next_step(EX, 1, "concept", "¿Qué es el MCM?")[1], "concept")

    def test_plan_rejects_invalid_length(self):
        with self.assertRaises(ValueError):
            rules.validate_exercises([EX])


if __name__ == "__main__":
    unittest.main()
