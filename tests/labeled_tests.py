import inspect
from dataclasses import dataclass
from typing import Callable, TypeVar, Generic

import pytest


T = TypeVar('T')

@dataclass
class Expected(Generic[T]):
    """Wrapper for expected test results to be shared across multiple test cases"""
    value: T

TestCase = tuple
TestGroup = list[Expected | TestCase]
TestCases = TestGroup | TestCase


def _validate_parameters(param_count: int, test_case: TestCase) -> None:
    if param_count > 1:
        if not isinstance(test_case, tuple):
            raise ValueError(f'Expected tuple of {param_count} parameters but got {test_case}')
        elif len(test_case) != param_count:
            raise ValueError(f'Expected {param_count} parameters but got {len(test_case)}: ({test_case})')


def labeled_tests(tests: dict[str, TestCases]):
    def decorator(test_func: Callable):
        parameter_names = inspect.signature(test_func).parameters.keys()
        param_count = len(parameter_names)
        labels = []
        test_data = []

        for group_label, test_cases in tests.items():
            if not isinstance(test_cases, list):
                test_cases = [test_cases]

            expected = None
            try:
                expected_case = next(case for case in test_cases if isinstance(case, Expected))
                expected = expected_case.value
                test_cases.remove(expected_case)
                found_expected = True
            except StopIteration:
                found_expected = False

            for test_case in test_cases if isinstance(test_cases, list) else [test_cases]:
                if found_expected:
                    test_case = (test_case, expected)
                _validate_parameters(param_count, test_case)
                labels.append(group_label)
                test_data.append(test_case)
        return pytest.mark.parametrize(', '.join(parameter_names), test_data, ids=labels)(test_func)

    return decorator
