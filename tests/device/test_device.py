import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.runtime.error.helper import NumpyErrorHelper


class TestDeice(unittest.TestCase):
    """
    python -OO -m unittest discover -p test_*.py -s tests/device
    """

    data = []

    @classmethod
    def tearDownClass(cls):
        print("\n")
        [f() for f in cls.data]

    @classmethod
    def print(cls, *args, **kwargs):
        cls.data.append(lambda: print(*args, **kwargs))

    def test_min(self):
        a = np.minimum(np.float32(-0.0), np.float32(0.0))
        b = np.fmin(np.float32(-0.0), np.float32(0.0))

        self.print(f"minimum(-0.0, 0.0): {a}")
        self.print(f"fmin(-0.0, 0.0): {b}")

    def test_cast_overflow(self):
        with NumpyErrorHelper("call") as err:
            a = np.float32(2**32).astype(np.uint32)
            msg = "" if len(err) == 0 else f", {err[-1][0]}"
            self.print(f"f32(2**32) as u32: {a}{msg}")

    def test_cast_negative(self):
        with NumpyErrorHelper("call") as err:
            a = np.float32(-1).astype(np.uint32)
            msg = "" if len(err) == 0 else f", {err[-1][0]}"
            self.print(f"f32(-1) as u32: {a}{msg}")
