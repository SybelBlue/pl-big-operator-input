import prairielearn.sympy_utils as psu
import sympy


def structured(operator, index, domain, body):
    encode = lambda value: psu.sympy_to_json(value, allow_sets=True)
    return {
        "_type": "operator_expression",
        "_version": 1,
        "operator": operator,
        "limits": "domain",
        "index": encode(index),
        "domain": encode(domain),
        "body": encode(body),
    }


def generate(data):
    k, x = sympy.symbols("k x")
    data["correct_answers"].update(
        {
            "sum": psu.sympy_to_json(sympy.Sum(k**2, (k, 1, 4))),
            "product": psu.sympy_to_json(sympy.Product(k, (k, 1, 4))),
            "integral": psu.sympy_to_json(sympy.Integral(x**2, (x, 0, 1))),
            "limit": psu.sympy_to_json(sympy.Limit(sympy.sin(x) / x, x, 0, dir="+")),
            "union": structured("union", k, sympy.FiniteSet(1, 2), sympy.FiniteSet(k)),
            "and": structured("and", k, sympy.FiniteSet(1, 2), k > 0),
        }
    )
