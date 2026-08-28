import random

import sympy


def generate(data):
    x = sympy.Symbol("x")
    exponent = random.randint(2, 5)
    upper = random.randint(2, 6)
    answer = sympy.Sum(x**exponent, (x, 0, upper))
    data["params"]["answer_latex"] = sympy.latex(answer)
    data["correct_answers"]["sum"] = str(answer)
