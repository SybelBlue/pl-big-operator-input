import prairielearn.sympy_utils as psu
import sympy


def generate(data):
    a, b, c, k, n, t = sympy.symbols("a b c k n t")
    theta = sympy.Symbol("theta")

    data["correct_answers"]["exact-server-sum"] = psu.sympy_to_json(
        sympy.Sum(a * k + b, (k, 0, n))
    )
    data["correct_answers"]["exact-server-integral"] = psu.sympy_to_json(
        sympy.Integral(t**2 + c, (t, a, b))
    )

    # The element's correct-answer attribute must override this value.
    data["correct_answers"]["greek-integral"] = psu.sympy_to_json(
        sympy.Integral(sympy.cos(theta), (theta, 0, sympy.pi))
    )
