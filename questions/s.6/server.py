import prairielearn.sympy_utils as psu
import sympy


def generate(data):
    theta = sympy.Symbol("theta")
    data["correct_answers"]["integral"] = psu.sympy_to_json(
        sympy.Integral(sympy.sin(theta), (theta, 0, sympy.pi))
    )
