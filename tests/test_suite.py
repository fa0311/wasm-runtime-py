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

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.entry import WasmExecEntry
from src.wasm.runtime.error.error import WasmCallStackExhaustedError, WasmRuntimeError, WasmUnimplementedError
from src.wasm.runtime.exec import WasmExec
from src.wasm.type.base import AnyType
from src.wasm.type.numeric.numpy.float import F32, F64
from src.wasm.type.numeric.numpy.int import I32, I64
from src.wasm.type.ref.base import ExternRef, FuncRef


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.CI = os.getenv("CI") == "true"
        self.__set_logger()
        if sys.version_info >= (3, 12):
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
        if self.CI:
            np.seterr(all="ignore")
            logging.basicConfig(level=logging.FATAL)
        else:
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
            elif cmd["type"] == "action":
                res[-1][2].append(cmd)
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
            data = WasmLoader().load(wasm)
            optimizer = WasmOptimizer().optimize(data)
            data = WasmExecEntry.entry(optimizer)

            for case, cmd in enumerate(cmds):
                param = {"name": name, "index": f"{index:04d}", "case": f"{case:04d}"}
                with self.subTest(**param):
                    self.__test_run(data, cmd)
        else:
            self.fail(f"expect: module, actual: {t}")

    def __test_index_case(self, name: str, index: int, case: int):
        t, wasm, cmds = self.__get_test_suite_data(name)[index]
        data = WasmLoader().load(wasm)
        optimizer = WasmOptimizer().optimize(data)
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
            elif cmd["type"] == "action":
                self.__test_run_assert_return(data, cmd)
            else:
                self.fail(f"expect: assert_return or assert_trap, actual: {cmd['type']}")
        except WasmUnimplementedError as e:
            self.skipTest(str(e))
        except WasmCallStackExhaustedError as e:
            if self.CI:
                self.skipTest(str(e))
            else:
                self.fail(str(e))

    def __test_run_assert_return(self, data: WasmExec, cmd: dict):
        field = bytes(cmd["action"]["field"], "utf-8")
        type_map = {
            "i32": lambda x: I32.from_str(x),
            "i64": lambda x: I64.from_str(x),
            "f32": lambda x: F32.from_str(x),
            "f64": lambda x: F64.from_str(x),
            "externref": lambda x: ExternRef.from_value(x if x != "null" else None),
            "funcref": lambda x: FuncRef.from_value(x if x != "null" else None),
        }
        args = cmd["action"]["args"]
        expect = cmd["expected"]
        numeric_args: list[AnyType] = [type_map[value["type"]](value["value"]) for value in args]
        numeric_expect: list[AnyType] = [type_map[value["type"]](value["value"]) for value in expect]
        assert data is not None
        runtime, res = data.start(
            field=field,
            param=numeric_args,
        )
        if len(res) != len(numeric_expect):
            self.fail(f"expect: {len(numeric_expect)}, actual: {len(res)}")
        for i, (r, e) in enumerate(zip(res, numeric_expect)):
            a, b = r.value, e.value
            if type(r) != type(e):
                self.fail(f"expect: {e.__class__}, actual: {r.__class__}")
            if a is None and b is None:
                continue
            if a < b or a > b:
                self.fail(f"expect: {b}, actual: {a}")

    def __test_run_assert_trap(self, data: WasmExec, cmd: dict):
        field = bytes(cmd["action"]["field"], "utf-8")
        type_map = {
            "i32": lambda x: I32.from_str(x),
            "i64": lambda x: I64.from_str(x),
            "f32": lambda x: F32.from_str(x),
            "f64": lambda x: F64.from_str(x),
            "externref": lambda x: ExternRef.from_value(x if x != "null" else None),
            "funcref": lambda x: FuncRef.from_value(x if x != "null" else None),
        }
        args = cmd["action"]["args"]
        text = cmd["text"]
        numeric_args: list[AnyType] = [type_map[value["type"]](value["value"]) for value in args]
        try:
            assert data is not None
            runtime, res = data.start(
                field=field,
                param=numeric_args,
            )
            self.fail(f"expect: {text}, actual: {res}")
        except WasmRuntimeError as e:
            if text != e.message:
                if isinstance(e, WasmCallStackExhaustedError):
                    raise e
                self.fail(f"expect: {cmd['text']}, actual: {e.message}")

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

    def test_i32_0_24(self):
        self.__test_index_case("i32", 0, 24)

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

    def test_call_indirect(self):
        self.__test_file("call_indirect")
        
    def test_call_indirect_0(self):
        self.__test_index("call_indirect", 0)

    def test_call_indirect_1(self):
        self.__test_index("call_indirect", 1)

    def test_call_indirect_1_2(self):
        self.__test_index_case("call_indirect", 1, 2)
    
    def test_call_indirect_1_9(self):
        self.__test_index_case("call_indirect", 1, 9)

    def test_return(self):
        self.__test_file("return")

    def test_if(self):
        self.__test_file("if")

    def test_loop(self):
        self.__test_file("loop")

    def test_load(self):
        self.__test_file("load")

    def test_local_tee(self):
        self.__test_file("local_tee")

    def test_func(self):
        self.__test_file("func")

    def test_endianness(self):
        self.__test_file("endianness")

    def test_align(self):
        self.__test_file("align")

    def test_left_to_right(self):
        self.__test_file("left-to-right")

    def test_memory(self):
        self.__test_file("memory")

    def test_unreachable(self):
        self.__test_file("unreachable")

    def test_unreached_valid(self):
        self.__test_file("unreached-valid")

    def test_unreached_invalid(self):
        self.__test_file("unreached-invalid")

    def test_unwind(self):
        self.__test_file("unwind")

    def test_ref_null(self):
        self.__test_file("ref_null")

    def test_traps(self):
        self.__test_file("traps")

    def test_table_sub(self):
        self.__test_file("table-sub")

    def test_table_set(self):
        self.__test_file("table_set")

    def test_table_get(self):
        self.__test_file("table_get")

    def test_ref_is_null(self):
        self.__test_file("ref_is_null")

    def test_table_fill(self):
        self.__test_file("table_fill")

    def test_table_grow(self):
        self.__test_file("table_grow")

    def test_table_size(self):
        self.__test_file("table_size")

    # def test_address(self):
    #     self.__test_file("address")

    # def test_float_exprs(self):
    #     self.__test_file("float_exprs")

    def test_float_memory(self):
        self.__test_file("float_memory")

    def test_memory_redundancy(self):
        self.__test_file("memory_redundancy")

    # def test_memory_fill(self):
    #     self.__test_file("memory_fill")

    # def test_memory_copy(self):
    #     self.__test_file("memory_copy")

    # def test_memory_init(self):
    #     self.__test_file("memory_init")

    # def test_memory_grow(self):
    #     self.__test_file("memory_grow")

    # def test_memory_size(self):
    #     self.__test_file("memory_size")

    # def test_memory_trap(self):
    #     self.__test_file("memory_trap")

    def test_nop(self):
        self.__test_file("nop")
