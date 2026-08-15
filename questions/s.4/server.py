import sympy


def generate(data):
    x = sympy.Symbol("x")
    data["correct_answers"]["integral"] = sympy.Integral(x**3, (x, 0, 2))
