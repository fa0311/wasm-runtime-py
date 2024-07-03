import unittest

import numpy as np


class TestDeice(unittest.TestCase):
    def test_min(self):
        a = np.minimum(np.float32(-0.0), np.float32(0.0))
        b = np.fmin(np.float32(-0.0), np.float32(0.0))

        aa = "<" if np.signbit(a) else ">"
        bb = "<" if np.signbit(b) else ">"

        print(f"minimum: -0.0 {aa} 0.0")
        print(f"fmin: -0.0 {bb} 0.0")

    def test_cast(self):
        a = np.float32(2**31).astype(np.uint32)
        c = np.float32(2**32).astype(np.uint32)
        e = np.float32(2**64).astype(np.uint32)

        print(f"2**31: {a}")
        print(f"2**32: {c}")
        print(f"2**64: {e}")
