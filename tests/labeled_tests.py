import inspect
from typing import Callable, Union, Any

import pytest


def labeled_tests(test_case_data: dict[str, Union[tuple[Any, ...], list[tuple[Any, ...]]]]):
    def decorator(test_func: Callable):
        params = ", ".join(inspect.signature(test_func).parameters.keys())
        labels = []
        test_data = []
        for key, value in test_case_data.items():
            for data in value if isinstance(value, list) else [value]:
                labels.append(key)
                test_data.append(data)
        return pytest.mark.parametrize(params, test_data, ids=labels)(test_func)
    return decorator
