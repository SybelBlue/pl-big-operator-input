import random

import prairielearn as pl
import sympy


def generate(data):
    t = sympy.Symbol("t")
    radius = random.randint(1, 5)
    constant = random.randint(1, 6)
    answer = sympy.Product(t**2 + constant, (t, -radius, radius))
    data["params"]["answer_latex"] = sympy.latex(answer)
    data["correct_answers"]["product"] = pl.to_json(answer)
