import sympy
from sympy.abc import k, n


def generate(data):
    data["correct_answers"]["sum"] = str(sympy.Sum(k**2, (k, 1, n)))
