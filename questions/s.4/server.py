import prairielearn.sympy_utils as psu
import sympy


def generate(data):
    x = sympy.Symbol("x")
    data["correct_answers"]["integral"] = psu.sympy_to_json(
        sympy.Integral(x**3, (x, 0, 2))  # type: ignore
    )
