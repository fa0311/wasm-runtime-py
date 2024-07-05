from typing import Callable, Optional

import numpy as np


class NumpyErrorHelper:
    def __init__(self, text, call_fn: Optional[Callable[[str, int], None]] = None):
        self.text = text
        self.call_stack = []
        self.call_fn = call_fn or self.call_stack_append

    def call_stack_append(self, x: str, y: int):
        self.call_stack.append((x, y))

    def __len__(self):
        return len(self.call_stack)

    def __getitem__(self, item):
        return self.call_stack[item]

    def __iter__(self):
        return iter(self.call_stack)

    def __enter__(self):
        self.last_conf = np.geterr()
        np.seterr(all=self.text)
        np.seterrcall(self.call_fn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        np.seterr(**self.last_conf)
        np.seterrcall(None)

    @staticmethod
    def seterr(text):
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                with NumpyErrorHelper(text):
                    return func(*args, **kwargs)

            return wrapper

        return decorator
