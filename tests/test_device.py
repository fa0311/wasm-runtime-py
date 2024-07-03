import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.runtime.error.helper import NumpyErrorHelper


class TestDeice(unittest.TestCase):
    def setUp(self):
        self.data = []

    def tearDown(self):
        [f() for f in self.data]

    def print(self, *args, **kwargs):
        self.data.append(lambda: print(*args, **kwargs))

    def test_min(self):
        a = np.minimum(np.float32(-0.0), np.float32(0.0))
        b = np.fmin(np.float32(-0.0), np.float32(0.0))

        self.print(f"minimum(-0.0, 0.0): {a}")
        self.print(f"fmin(-0.0, 0.0): {b}")

    def test_cast(self):
        a = np.float32(2**31).astype(np.uint32)
        c = np.float32(2**32).astype(np.uint32)
        e = np.float32(2**64).astype(np.uint32)

        self.print(f"2**31: {a}")
        self.print(f"2**32: {c}")
        self.print(f"2**64: {e}")

    def test_cast_error(self):
        with NumpyErrorHelper("raise"):
            try:
                np.float32(2**32).astype(np.uint32)
                self.print("No error")
            except FloatingPointError as e:
                self.print(e)
