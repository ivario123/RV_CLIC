from functools import wraps
from .simulators import _run
from typing import List
import inspect
import os
import traceback


def str_rpr(cls):
    """
    Sets the classes' __repr__ to return self.__str__.
    """
    if cls.__str__ == None:
        cls.__str__ = lambda self: f"<{cls.name}>"
    cls.__repr__ = cls.__str__
    return cls


OK_GREEN = "\033[92m"
OK_BLUE = "\033[94m"
WARNING = "\033[93m"
FAIL = "\033[91m"
GOLD = "\033[33m"
ENDC = "\033[0m"
from enum import Enum


class InfoType(Enum):
    ELABORATOR = 0
    MODULE = 1


def info(type: InfoType = InfoType.ELABORATOR, **info_kwargs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if type == InfoType.ELABORATOR:
                print(OK_GREEN + "[INFO] " + ENDC + func.__name__ + " called")
            elif type == InfoType.MODULE:
                print(OK_GREEN + "[INFO] ")
                print(
                    f"Instantiating module {info_kwargs['module']} with the following parameters:\n{'{'}\n\t"
                    + "\n\t".join(
                        [str(key) + " = " + str(value) for key, value in kwargs.items()]
                    )
                    + "\n}"
                    + ENDC,
                )
            ret = func(*args, **kwargs)
            print(f"{'-'*50}\n{OK_BLUE}{func.__name__} returned {ret}{ENDC}\n{'-'*50}")

        return wrapper

    return decorator


import sys
from io import StringIO


class ContextManager(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def simulation(imports: List[str] = ["Tick", "Settle", "Simulator"], **kwargs):
    """
    Performs function analysis to extract the tests and run them in a simulator.

    **kwargs:
        model_name = model

    Example:
    ```python
    model = Module()
    @simulation(model = model)
    def model_test():
        def test_1():
            yield Tick()
            yield Settle()
            yield Tick()
            yield Settle()
            assert model.a == 1

        def test_2():
            yield Tick()
            yield Settle()
            yield Tick()
            yield Settle()
            assert model.a == 2
    ```
    It replaces the model_test function with a new function that returns a list of the tests.
    and runs that instead.
    Then it runs that list of tests in a simulator.



    """
    # We never get this far without simulating
    sim = os.environ.get("SIMULATE", "0")
    assert (
        len(kwargs) == 1
    ), "Only one keyword argument is allowed. Example: @simulation(model = model)"
    model_name = list(kwargs.keys())[0]
    base_model = list(kwargs.values())[0]
    grp_name = base_model.__class__.__name__.upper().replace("_", " ")

    def decorator(func):
        if sim not in ["1", func.__name__]:

            def _unused(*_):
                pass

            return _unused

        function_code = inspect.getsource(func).split("\n")

        # Extract all lines that contain def test_
        test_lines = [
            id + 1 for id, line in enumerate(function_code) if "@test" in line
        ]
        # extract function names
        # Using regex to match def (function name)(args) and extract the function name
        import re

        test_names = [
            re.search(r"def\s(\w+)\(", function_code[line]) for line in test_lines
        ]
        # Handle None case
        test_names = [test.group(1) for test in test_names if test is not None]

        # Generate new function that returns a list of the tests
        def rebuild(function_code):
            """
            Generates new code for each test case that imports
            the needed parts of the amaranth library.
            """
            # Check if code is indented with spaces or tabs

            def n_indents(x):
                for i, c in enumerate(x):
                    if c != " ":
                        return i
                return 0

            indent = lambda x, y: " " * n_indents(y) + x

            # Add a line after the def test_... that imports Tick, Settle and Simulator from amaranth
            index = 0
            for i, line in enumerate(function_code):
                if index >= len(test_names):
                    break
                if test_names[index] in line:
                    j = 0
                    # Locate last line of function def
                    for j in range(i, len(function_code)):
                        if ":" in function_code[j]:
                            break
                    index += 1
                    # Insert imports
                    function_code[j] = "\n".join(
                        [
                            line,
                            indent(
                                f"from amaranth.sim import {', '.join(imports)}",
                                function_code[j + 1],
                            )[n_indents(line) :],
                        ]
                    )
            # Increment to next test
            index += 1
            # Remove @test decorators
            function_code = [line for line in function_code if "@test" not in line]
            # Indent level of main function
            first_line_indent = len(function_code[2]) - len(function_code[2].lstrip())
            # Unindent all x by the indent level of the first line of the function
            unindent = lambda x: x[first_line_indent:]
            # unindent all lines and delete the @simulation and def lines
            code = "\n".join(map(unindent, function_code[2:]))

            # Write code to file
            with open("latest_test_file.py", "w") as f:
                f.write(code)

            # Return code
            return code

        def sim_run(*_, **__):
            """
            Actual simulation code, this is the function that will be
            used in the end.
            """

            # Build new function that returns the tests
            code = rebuild(function_code)

            # Place model_name=base_model in the global namespace
            globals()[model_name] = base_model

            # Generate test functions
            exec(code, globals(), locals())

            # Run tests
            errors = []
            passcount = 0
            for test in test_names:
                func = eval(test)
                fname = func.__name__.replace("_", " ")
                print(f"Running test {fname}")
                try:
                    _run(globals()[model_name], eval(test))
                    print(f"{OK_GREEN}{'-'*50}")
                    print(f"Test {fname} for {grp_name} passed")
                    print(f"{'-'*50}{ENDC}")
                    passcount += 1
                except Exception as e:
                    print(f"{FAIL}{'-'*50}")
                    print(f"Test {fname} for {grp_name} failed")
                    print(f"{'-'*50}{ENDC}")
                    print(e)
                    print(traceback.format_exc())
                    errors.append(e)
            if len(errors) == 0:
                print(
                    f"""{'-'*50}
{OK_BLUE}All {passcount} tests for {grp_name} passed{ENDC}
{'-'*50}"""
                )
            else:
                print(
                    f"""{'-'*50}
Results for {grp_name}:
\t{FAIL} {len(errors)} tests failed{ENDC}
\t{OK_BLUE} {passcount} tests passed
{ENDC}{'-'*50}"""
                )

            # Restore namespace
            globals().pop(model_name)

        return sim_run

    return decorator


def test(func):
    """
    Pure marker decorator that marks a function as a test.
    """
    return func


def simulator(func):
    """
    Decorator that is quite similar to pytests test framework.
    It runs the function in a simulator and intercepts the output.
    If the output contains the word error it will print the error and the number of errors.
    """
    sim = os.environ.get("SIMULATE", "0")
    if sim != "0":

        def wrapper(*args, **kwargs):
            print(f"Running {func.__name__}")
            errors = []
            with ContextManager() as out:
                func(*args, **kwargs)
            for line in out:
                print(line)
                if "error" in line.lower():
                    errors.append(line)

            if len(errors) > 0:
                print(f"{FAIL}{len(errors)} Errors found during simulation{ENDC}")
                for error in errors:
                    print(f"{GOLD}*{ENDC} {FAIL}{error}{ENDC}")
                print()
            else:
                print(f"{OK_GREEN}No errors found during simulation{ENDC}")

        return wrapper
    else:
        print(sim)

        def _unused(*_):
            print(
                f"{FAIL}Set $Env:SIMULATE to 1 or a specific simulation name to run simulations and pass -s to the clic{ENDC}"
            )

        return _unused
