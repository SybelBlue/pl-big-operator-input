import sympy


def generate(data):
    theta = sympy.Symbol("theta")
    data["correct_answers"]["integral"] = sympy.Integral(
        sympy.sin(theta), (theta, 0, sympy.pi)
    )
