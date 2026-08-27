import random

import prairielearn as pl
import sympy


def generate(data):
    theta = sympy.Symbol("theta")
    coefficient = random.randint(1, 5)
    frequency = random.randint(1, 4)
    answer = sympy.Limit(
        coefficient * sympy.sin(frequency * theta) / theta,
        theta,
        0,
        dir="+",
    )
    data["params"]["answer_latex"] = sympy.latex(answer)
    data["correct_answers"]["limit"] = pl.to_json(answer)
