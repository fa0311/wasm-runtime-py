import sys
import time
import unittest
from pathlib import Path
from typing import Callable

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.entry import WasmExecEntry
from src.wasm.type.numeric.numpy.int import I64


class StopWatch:
    def __init__(self, p: Callable):
        self.p = p

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.result = time.time() - self.start
        self.p(f"Time: {self.result:.3f}sec")

    def average(self, fn: Callable, n: int = 10):
        min, max, total = float("inf"), 0, 0
        for _ in range(n):
            with self.__class__(lambda _: None) as x:
                fn()
            min = min if min < x.result else x.result
            max = max if max > x.result else x.result
            total += x.result
        self.p(f"Time: {min:.3f}sec ~ {max:.3f}sec (average: {total/n:.3f}sec)")


class TestBenchmark(unittest.TestCase):
    """
    $env:WASM_FAST="true"
    python -OO -m unittest discover -p test_*.py -s tests/benchmark
    """

    data = []

    @classmethod
    def tearDownClass(cls):
        print("\n")
        [f() for f in cls.data]

    @classmethod
    def print(cls, *args, **kwargs):
        cls.data.append(lambda: print(*args, **kwargs))

    def test_fib(self):
        with open(".cache/call/call.0.wasm", "rb") as f:
            data = WasmLoader().load(f.read())
            optimizer = WasmOptimizer().optimize(data)
            data = WasmExecEntry.entry(optimizer)

        def test():
            data.start(b"fib", [I64.from_int(22)])

        StopWatch(self.print).average(test)
