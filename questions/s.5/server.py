import prairielearn.sympy_utils as psu
import sympy


def generate(data):
    t = sympy.Symbol("t")
    data["correct_answers"]["integral"] = psu.sympy_to_json(
        sympy.Integral(t**2 + 1, (t, -1, 1))
    )
