import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.type.main import SignedI32


class TestUnit(unittest.TestCase):
    def test_signed_i32(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(3)
        self.assertEqual((a % b).value, -1)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a % b).value, 1)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a % b).value, -1)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(3)
        self.assertEqual((a // b).value, -3)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a // b).value, -3)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a // b).value, 2)
