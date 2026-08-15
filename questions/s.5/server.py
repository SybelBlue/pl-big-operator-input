import sympy


def generate(data):
    t = sympy.Symbol("t")
    data["correct_answers"]["integral"] = sympy.Integral(t**2 + 1, (t, -1, 1))
