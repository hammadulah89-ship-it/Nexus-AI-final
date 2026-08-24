"""
Pillar 3: Exact Deterministic Mathematical Calculator & SymPy Solver.
Solves algebra, calculus, derivatives, integrals, fractions, and matrix calculations with 100% precision.
"""

import sympy as sp
from typing import Dict, Any, Optional

class ExactMathEngine:
    def __init__(self):
        self.x, self.y, self.z, self.t = sp.symbols('x y z t')

    def evaluate(self, expression_str: str) -> Dict[str, Any]:
        """
        Evaluates a mathematical query or expression deterministically.
        Supports algebra, calculus, integration, derivation, and simplification.
        """
        try:
            expr_clean = expression_str.strip()
            
            # Common conversions
            expr_clean = expr_clean.replace("^", "**")
            
            # Evaluate using SymPy parser
            parsed = sp.sympify(expr_clean, evaluate=True)
            
            exact_val = str(parsed)
            numeric_val = None
            try:
                numeric_val = float(parsed.evalf())
            except Exception:
                pass

            # LaTeX representation for math display
            latex_repr = sp.latex(parsed)

            return {
                "success": True,
                "input": expression_str,
                "exact_result": exact_val,
                "numeric_approx": numeric_val,
                "latex": latex_repr,
                "formatted": f"{exact_val}" + (f" (≈ {numeric_val:.6f})" if numeric_val is not None and str(numeric_val) != exact_val else "")
            }
        except Exception as e:
            return {
                "success": False,
                "input": expression_str,
                "error": str(e),
                "formatted": f"Math error: {str(e)}"
            }

    def solve_equation(self, eq_str: str, var_str: str = "x") -> Dict[str, Any]:
        """Solves algebraic equations for a specified variable."""
        try:
            var = sp.Symbol(var_str)
            if "=" in eq_str:
                lhs_str, rhs_str = eq_str.split("=", 1)
                lhs = sp.sympify(lhs_str.replace("^", "**"))
                rhs = sp.sympify(rhs_str.replace("^", "**"))
                eq = sp.Eq(lhs, rhs)
            else:
                eq = sp.sympify(eq_str.replace("^", "**"))

            solutions = sp.solve(eq, var)
            solutions_str = [str(s) for s in solutions]
            
            return {
                "success": True,
                "equation": eq_str,
                "variable": var_str,
                "solutions": solutions_str,
                "formatted": f"Solutions for {var_str}: {', '.join(solutions_str)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "formatted": f"Equation solving error: {str(e)}"
            }
