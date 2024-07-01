from typing import Callable

import numpy as np


class NumpyErrorHelper:
    def __init__(self, text):
        self.text = text

    def __enter__(self):
        self.last = np.geterr()
        np.seterr(all=self.text)

    def __exit__(self, exc_type, exc_val, exc_tb):
        np.seterr(**self.last)

    @staticmethod
    def seterr(text):
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                with NumpyErrorHelper(text):
                    return func(*args, **kwargs)

            return wrapper

        return decorator
