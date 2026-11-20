"""Reconocimiento de la operación de fila entre dos pasos."""

from fractions import Fraction

from prettycalc.core.cramer import solve_cramer
from prettycalc.core.elimination import gauss_jordan_elimination
from prettycalc.core.lu_decomposition import lu_decompose, plu_decompose
from prettycalc.core.matrix_inversion import matrix_inverse
from prettycalc.core.step_diff import (
    ADD,
    SCALE,
    SWAP,
    changed_cells,
    contradiction_rows,
    detect_row_operation,
    detect_step_operation,
    is_echelon,
    leading_entries,
    replaced_column,
)
from prettycalc.core.types import Matrix, Vector


def test_changed_cells_only_lists_entries_that_changed():
    before = Matrix([[1, 2], [0, 3]])
    after = Matrix([[1, 2], [0, 5]])
    assert changed_cells(before, after) == ((1, 1),)
    assert changed_cells(before, Matrix([[1, 2, 3], [4, 5, 6]])) is None


def test_detects_swap():
    before = Matrix([[0, 1, 2], [3, 4, 5], [6, 7, 8]])
    after = Matrix([[3, 4, 5], [0, 1, 2], [6, 7, 8]])
    op = detect_row_operation(before, after)
    assert op.kind == SWAP and set(op.rows()) == {0, 1}


def test_detects_scale_with_exact_factor():
    before = Matrix([[2, 4, 6], [1, 1, 1]])
    after = Matrix([[1, 2, 3], [1, 1, 1]])
    op = detect_row_operation(before, after)
    assert op.kind == SCALE and op.target == 0 and op.factor == Fraction(1, 2)


def test_detects_add_multiple_and_prefers_actor_row():
    before = Matrix([[1, 1, 4], [2, -1, 4], [2, 2, 8]])
    after = Matrix([[1, 1, 4], [0, -3, -4], [2, 2, 8]])
    op = detect_row_operation(before, after, actor_row=0)
    assert (op.kind, op.target, op.source, op.factor) == (ADD, 1, 0, Fraction(-2))
    # Sin pista, la fila 2 (proporcional a la 0) también explicaría el cambio;
    # la pista desambigua y el resultado sigue siendo verdad.
    op = detect_row_operation(before, after, actor_row=2)
    assert (op.kind, op.source, op.factor) == (ADD, 2, Fraction(-1))


def test_rejects_changes_that_are_not_one_operation():
    before = Matrix([[1, 0], [0, 1], [1, 1]])
    after = Matrix([[2, 0], [0, 3], [1, 1]])
    assert detect_row_operation(before, after) is None
    assert detect_row_operation(Matrix([[1, 2]]), Matrix([[1, 3]])) is None


def test_every_gauss_jordan_step_matches_its_metadata():
    system = Matrix([[0, 1, 1, 4], [2, -1, 1, 4], [1, 2, -1, 3]])
    _result, tracer = gauss_jordan_elimination(system, split_col=3)
    steps = tracer.get_steps()
    assert len(steps) > 3
    for previous, step in zip(steps, steps[1:]):
        op = detect_step_operation(
            previous.matrix,
            step.matrix,
            split_col=step.split_col,
            actor_row=step.actor_row,
            affected_rows=step.affected_rows,
        )
        assert op is not None, step.heuristic_text
        assert set(op.rows()) == set(step.affected_rows) | ({op.source} if op.kind == SWAP else set())
        if step.actor_row is not None:
            assert op.kind == ADD and op.source == step.actor_row
        elif len(step.affected_rows) == 2:
            assert op.kind == SWAP
        else:
            assert op.kind == SCALE
        # La operación reconstruye exactamente la matriz del paso.
        rebuilt = [[previous.matrix.get(r, c) for c in range(step.matrix.cols)] for r in range(step.matrix.rows)]
        if op.kind == SWAP:
            rebuilt[op.target], rebuilt[op.source] = rebuilt[op.source], rebuilt[op.target]
        elif op.kind == SCALE:
            rebuilt[op.target] = [op.factor * v for v in rebuilt[op.target]]
        else:
            rebuilt[op.target] = [a + op.factor * b for a, b in zip(rebuilt[op.target], rebuilt[op.source])]
        assert Matrix(rebuilt) == step.matrix


def test_inverse_steps_are_recognised_over_the_whole_augmented_matrix():
    result = matrix_inverse(Matrix([[2, 1], [5, 3]]))
    steps = result.tracer.get_steps()
    for previous, step in zip(steps, steps[1:]):
        if previous.matrix.shape != step.matrix.shape:
            continue
        op = detect_step_operation(previous.matrix, step.matrix, split_col=step.split_col, actor_row=step.actor_row)
        if step.affected_rows:
            assert op is not None
            assert op.columns == (0, step.matrix.cols)


def test_lu_steps_recognise_the_row_operation_on_u_and_the_multiplier_on_l():
    result = lu_decompose(Matrix([[2, 1, 1], [4, -6, 0], [-2, 7, 2]]))
    steps = result.tracer.get_steps()
    n = 3
    for previous, step in zip(steps, steps[1:]):
        if not step.affected_rows or step.actor_row is None:
            continue
        op = detect_step_operation(
            previous.matrix, step.matrix, split_col=step.split_col, actor_row=step.actor_row
        )
        assert op is not None and op.kind == ADD
        assert op.columns == (n, 2 * n)
        target, source = step.affected_rows[0], step.actor_row
        assert (op.target, op.source) == (target, source)
        # El multiplicador queda en L(target, source) y vale −k.
        changed_l = [cell for cell in changed_cells(previous.matrix, step.matrix) if cell[1] < n]
        assert changed_l == [(target, source)]
        assert step.matrix.get(target, source) == -op.factor


def test_plu_swap_is_recognised():
    result = plu_decompose(Matrix([[0, 2, 1], [1, 1, 1], [2, 1, 0]]))
    steps = result.tracer.get_steps()
    kinds = []
    for previous, step in zip(steps, steps[1:]):
        if len(step.affected_rows) == 2 and step.actor_row is None and previous.matrix.shape == step.matrix.shape:
            op = detect_step_operation(previous.matrix, step.matrix, split_col=step.split_col)
            kinds.append(op.kind if op else None)
    assert SWAP in kinds


def test_cramer_column_replacement_is_the_b_column():
    A = Matrix([[2, 1], [1, 3]])
    b = Vector([3, 5])
    result = solve_cramer(A, b)
    steps = result.tracer.get_steps()
    base = steps[0].matrix
    found = []
    for step in steps:
        col = replaced_column(base, step.matrix, step.highlight_cells)
        if col is not None:
            found.append(col)
            assert [step.matrix.get(r, col) for r in range(2)] == [Fraction(3), Fraction(5)]
    assert sorted(set(found)) == [0, 1]


def test_leading_entries_and_echelon_form():
    rref = Matrix([[1, 0, 2, 3], [0, 1, -1, 1], [0, 0, 0, 0]])
    assert leading_entries(rref, 3) == ((0, 0), (1, 1))
    assert is_echelon(rref, 3)
    assert not is_echelon(Matrix([[0, 1], [1, 0]]))
    assert contradiction_rows(Matrix([[1, 0, 2], [0, 0, 5]]), 2) == (1,)
    assert contradiction_rows(Matrix([[1, 0, 2], [0, 0, 0]]), 2) == ()
