import inspect
from typing import Callable, Any

import pytest


def labeled_tests(test_case_data: dict[str, tuple|list[tuple|Any]]):
    def decorator(test_func: Callable):
        params = inspect.signature(test_func).parameters.keys()
        labels = []
        test_data = []
        for key, value in test_case_data.items():
            for data in value if isinstance(value, list) else [value]:
                labels.append(key)
                if len(params) > 1:
                    if not isinstance(data, tuple):
                        raise ValueError(f'Expected tuple of {len(params)} parameters but got {data}')
                    elif len(data) != len(params):
                        raise ValueError(f'Expected {len(params)} parameters but got {len(data)}: ({data})')
                test_data.append(data)
        return pytest.mark.parametrize(', '.join(params), test_data, ids=labels)(test_func)
    return decorator
