"""Pruebas unitarias para el sistema de trazabilidad de pasos StepTracer."""

import unittest
from fractions import Fraction

from prettycalc.core.types import Matrix
from prettycalc.core.tracer import CalculationStep, StepTracer


class TestStepTracer(unittest.TestCase):
    """Pruebas para StepTracer y CalculationStep."""

    def test_record_initial_and_subsequent_steps(self):
        m0 = Matrix([[1, 2, 3], [4, 5, 6]])
        tracer = StepTracer(split_col=2)

        init_step = tracer.record_initial(m0)
        self.assertEqual(init_step.step_number, 0)
        self.assertEqual(init_step.matrix, m0)
        self.assertIsNone(init_step.pivot_pos)
        self.assertEqual(init_step.split_col, 2)

        # Mutar matriz para el paso 1
        m1 = Matrix([[1, 2, 3], [0, -3, -6]])
        step1 = tracer.record_step(
            matrix=m1,
            latex_formula="f_{2} \\underset{\\sim}\\rightarrow -4f_{1} + f_{2}",
            heuristic_text="Se multiplicó la Fila 1 por -4 y se sumó a la Fila 2.",
            pivot_pos=(0, 0),
        )
        self.assertEqual(step1.step_number, 1)
        self.assertEqual(step1.pivot_pos, (0, 0))
        self.assertEqual(len(tracer), 2)

        steps = tracer.get_steps()
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].step_number, 0)
        self.assertEqual(steps[1].step_number, 1)

    def test_step_immutability(self):
        m = Matrix([[1, 2], [3, 4]])
        tracer = StepTracer()
        step = tracer.record_initial(m)
        # Modificar m original no debe alterar el snapshot del paso
        m.set(0, 0, 99)
        self.assertEqual(step.matrix.get(0, 0), Fraction(1, 1))

    def test_tracer_clear_and_iteration(self):
        tracer = StepTracer()
        m = Matrix([[1, 2]])
        tracer.record_initial(m)
        tracer.record_step(m, "f1", "h1")
        self.assertEqual(len(tracer), 2)

        step_nums = [s.step_number for s in tracer]
        self.assertEqual(step_nums, [0, 1])

        tracer.clear()
        self.assertEqual(len(tracer), 0)


if __name__ == "__main__":
    unittest.main()
