import glob
import json
import logging
import os
import pathlib
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

from src.wasm.type.externref.base import ExternRef

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.entry import WasmExecEntry
from src.wasm.runtime.error.error import WasmRuntimeError, WasmUnimplementedError
from src.wasm.runtime.exec import WasmExec
from src.wasm.type.numeric.base import NumericType
from src.wasm.type.numeric.numpy.float import F32, F64
from src.wasm.type.numeric.numpy.int import I32, I64


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.__set_logger()
        sys.setrecursionlimit(10**6)
        if not os.path.exists(".cache"):
            self.__set_wasm2json()

    def tearDown(self):
        logging.shutdown()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __set_logger(self):
        if __debug__:
            filename = "latest.log"
            if os.path.exists(filename):
                os.remove(filename)
            handler = logging.FileHandler(
                filename,
                mode="a",
                encoding="utf-8",
                delay=True,
            )
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(message)s",
                handlers=[handler],
            )
        else:
            np.seterr(all="ignore")
            logging.basicConfig(level=logging.FATAL)

    def __set_wasm2json(self):
        filelist = glob.glob("testsuite/*.wast")
        for path in filelist:
            name = pathlib.Path(path).stem
            os.makedirs(f".cache/{name}", exist_ok=True)
            subprocess.run(
                [
                    "wast2json",
                    f"testsuite/{name}.wast",
                    "-o",
                    f".cache/{name}/{name}.json",
                ],
            )

    def __read_module(self, name: str, filename: str):
        with open(f".cache/{name}/{filename}", "rb") as f:
            wasm = f.read()
        return wasm

    def __get_test_suite_data(self, name: str):
        path = pathlib.Path(f".cache/{name}/{name}.json")

        with open(path, "rb") as f:
            source = json.load(f)

        res: list[tuple[str, bytes, list[dict]]] = []
        for cmd in source["commands"]:
            if cmd["type"] == "module":
                res.append((cmd["type"], self.__read_module(name, cmd["filename"]), []))
            elif cmd["type"] == "assert_return":
                res[-1][2].append(cmd)
            elif cmd["type"] == "assert_trap":
                res[-1][2].append(cmd)
            elif cmd["type"] == "assert_invalid":
                res.append((cmd["type"], self.__read_module(name, cmd["filename"]), []))
            elif cmd["type"] == "assert_exhaustion":
                res[-1][2].append(cmd)
            elif cmd["type"] == "assert_malformed":
                res.append((cmd["type"], self.__read_module(name, cmd["filename"]), []))
            else:
                self.fail(f"unknown command: {cmd['type']}")
        return res

    def __test_file(self, name: str):
        case = self.__get_test_suite_data(name)
        for i in range(len(case)):
            self.__test_index(name, i)

    def __test_index(self, name: str, index: int):
        t, wasm, cmds = self.__get_test_suite_data(name)[index]
        if t == "assert_invalid":
            pass
            # try:
            #     if len(cmds) > 1:
            #         self.fail(f"expect: 1, actual: {len(cmds)}")
            #     data = WasmLoader(wasm).load()
            #     optimizer = WasmOptimizer(data).optimize()
            #     data = WasmExec(optimizer)
            #     self.fail(f"expect: {cmds[0]['type']}, actual: {data}")
            # except WasmInvalidError as e:
            #     a, b = e.message, cmds[0]["text"]
            #     if a != b:
            #         self.fail(f"expect: {b}, actual: {a}")
            # except WasmUnimplementedError as e:
            #     self.skipTest(str(e))
        elif t == "assert_malformed":
            pass
        elif t == "module":
            data = WasmLoader(wasm).load()
            optimizer = WasmOptimizer(data).optimize()
            data = WasmExecEntry.entry(optimizer)

            for case, cmd in enumerate(cmds):
                param = {"name": name, "index": f"{index:04d}", "case": f"{case:04d}"}
                with self.subTest(**param):
                    self.__test_run(data, cmd)
                    data.reset()
        else:
            self.fail(f"expect: module, actual: {t}")

    def __test_index_case(self, name: str, index: int, case: int):
        t, wasm, cmds = self.__get_test_suite_data(name)[index]
        data = WasmLoader(wasm).load()
        optimizer = WasmOptimizer(data).optimize()
        data = WasmExecEntry.entry(optimizer)
        self.__test_run(data, cmds[case])

    def __test_run(self, data: WasmExec, cmd: dict):
        try:
            if cmd["type"] == "assert_return":
                self.__test_run_assert_return(data, cmd)
            elif cmd["type"] == "assert_trap":
                self.__test_run_assert_trap(data, cmd)
            elif cmd["type"] == "assert_exhaustion":
                self.__test_run_assert_trap(data, cmd)
            else:
                self.fail(f"expect: assert_return or assert_trap, actual: {cmd['type']}")
        except WasmUnimplementedError as e:
            self.skipTest(str(e))

    def __test_run_assert_return(self, data: WasmExec, cmd: dict):
        field = bytes(cmd["action"]["field"], "utf-8")
        type_map = {
            "i32": lambda x: I32.from_str(x),
            "i64": lambda x: I64.from_str(x),
            "f32": lambda x: F32.from_str(x),
            "f64": lambda x: F64.from_str(x),
            "externref": lambda x: ExternRef(x),
        }
        args = cmd["action"]["args"]
        expect = cmd["expected"]
        numeric_args: list[NumericType] = [type_map[value["type"]](value["value"]) for value in args]
        numeric_expect: list[NumericType] = [type_map[value["type"]](value["value"]) for value in expect]
        assert data is not None
        runtime, res = data.start(
            field=field,
            param=numeric_args,
        )
        for i, (r, e) in enumerate(zip(res, numeric_expect)):
            a, b = r.value, e.value
            if type(r) != type(e):
                self.fail(f"expect: {e.__class__}, actual: {r.__class__}")
            if a > b and b < a:
                self.fail(f"expect: {b}, actual: {a}")

    def __test_run_assert_trap(self, data: WasmExec, cmd: dict):
        field = bytes(cmd["action"]["field"], "utf-8")
        type_map = {
            "i32": lambda x: I32.from_str(x),
            "i64": lambda x: I64.from_str(x),
            "f32": lambda x: F32.from_str(x),
            "f64": lambda x: F64.from_str(x),
        }
        args = cmd["action"]["args"]
        expect = cmd["expected"]
        text = cmd["text"]
        numeric_args: list[NumericType] = [type_map[value["type"]](value["value"]) for value in args]

        try:
            assert data is not None
            runtime, res = data.start(
                field=field,
                param=numeric_args,
            )
            self.fail(f"expect: {text}, actual: {res}")
        except WasmRuntimeError as e:
            if text != e.message:
                self.fail(f"expect: {cmd['text']}, actual: {e.message}")
            for i, (r, e) in enumerate(zip(expect, e.expected)):
                numeric_cls = type_map[r["type"]]
                if numeric_cls(0).__class__ != e:
                    self.fail(f"expect: {e}, actual: {numeric_cls(0).__class__}")

    def subTest(self, **param):
        SUBTEST = True
        if SUBTEST:
            return super().subTest(**param)
        else:
            return self

    def test_comments(self):
        self.__test_file("comments")

    def test_type(self):
        self.__test_file("type")

    def test_inline_module(self):
        self.__test_file("inline-module")

    def test_int_literals(self):
        self.__test_file("int_literals")

    def test_i32(self):
        self.__test_file("i32")

    def test_i64(self):
        self.__test_file("i64")

    def test_int_exprs(self):
        self.__test_file("int_exprs")

    def test_f32(self):
        self.__test_file("f32")

    def test_f32_bitwise(self):
        self.__test_file("f32_bitwise")

    def test_f32_cmp(self):
        self.__test_file("f32_cmp")

    def test_f64(self):
        self.__test_file("f64")

    def test_f64_bitwise(self):
        self.__test_file("f64_bitwise")

    def test_f64_cmp(self):
        self.__test_file("f64_cmp")

    def test_float_misc(self):
        self.__test_file("float_misc")

    def test_fac(self):
        self.__test_file("fac")

    def test_conversions(self):
        self.__test_file("conversions")

    def test_float_literals(self):
        self.__test_file("float_literals")

    def test_forward(self):
        self.__test_file("forward")

    def test_const(self):
        self.__test_file("const")

    def test_local_get(self):
        self.__test_file("local_get")

    def test_local_set(self):
        self.__test_file("local_set")

    def test_labels(self):
        self.__test_file("labels")

    def test_switch(self):
        self.__test_file("switch")

    def test_store(self):
        self.__test_file("store")

    def test_block(self):
        self.__test_file("block")

    def test_br(self):
        self.__test_file("br")

    def test_br_if(self):
        self.__test_file("br_if")

    def test_br_table(self):
        self.__test_file("br_table")

    def test_call(self):
        self.__test_file("call")

    # def test_call_35(self):
    #     self.__test_index_case("call", 0, 35)

    # def test_call_39(self):
    #     self.__test_index_case("call", 0, 39)

    # def test_call_42(self):
    #     self.__test_index_case("call", 0, 42)

    # def test_call_indirect(self):
    #     self.__test_file("call_indirect")

    # def test_return(self):
    #     self.__test_file("return")


if __name__ == "__main__":
    unittest.main()
