from typing import Any, Dict, Tuple
import contextlib
import traceback
import ast
import io

class SimpleCodeExecutor:
    """
    A simple code executor that runs Python code with state persistence.
    This executor maintains a global and local state between executions,
    allowing for variables to persist across multiple code runs.
    NOTE: not safe for production use! Use with caution.
    """

    def __init__(self, locals: Dict[str, Any], globals: Dict[str, Any]):
        """
        Initialize the code executor.
        Args:
            locals: Local variables to use in the execution context
            globals: Global variables to use in the execution context
        """
        # State that persists between executions
        self.globals = globals
        self.locals = locals

    def execute(self, code: str) -> Tuple[bool, str, Any]:
        """
        Execute Python code and capture output and return values.
        Args:
            code: Python code to execute
        Returns:
            Dict with keys `success`, `output`, and `return_value`
        """
        # Capture stdout and stderr
        stdout = io.StringIO()
        stderr = io.StringIO()

        output = ""
        return_value = None
        try:
            # Execute with captured output
            with contextlib.redirect_stdout(
                stdout
            ), contextlib.redirect_stderr(stderr):
                # Try to detect if there's a return value (last expression)
                try:
                    tree = ast.parse(code)
                    last_node = tree.body[-1] if tree.body else None

                    # If the last statement is an expression, capture its value
                    if isinstance(last_node, ast.Expr):
                        # Split code to add a return value assignment
                        last_line = code.rstrip().split("\n")[-1]
                        exec_code = (
                            code[: -len(last_line)]
                            + "\n__result__ = "
                            + last_line
                        )

                        # Execute modified code
                        exec(exec_code, self.globals, self.locals)
                        return_value = self.locals.get("__result__")
                    else:
                        # Normal execution
                        exec(code, self.globals, self.locals)
                except:
                    # If parsing fails, just execute the code as is
                    exec(code, self.globals, self.locals)

            # Get output
            output = stdout.getvalue()
            if stderr.getvalue():
                output += "\n" + stderr.getvalue()

        except Exception as e:
            # Capture exception information
            output = f"Error: {type(e).__name__}: {str(e)}\n"
            output += traceback.format_exc()

        if return_value is not None:
            output += "\n\n" + str(return_value)

        return output