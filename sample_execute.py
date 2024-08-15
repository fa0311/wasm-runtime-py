import logging
import os

import numpy as np

from src.tools.byte import ByteReader
from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.wasi import FS, Wasi, WasiBase, WasiExportHelperUtil, WasiResult
from src.wasm.type.numeric.numpy.int import I32


def set_logger():
    np.seterr(all="ignore")
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
    return True


def to_model(bin: bytes):
    data = ByteReader(bin)
    expr = WasmLoader().code_section_instructions(data)
    optimize = WasmOptimizer().expr(expr)
    return optimize


class Env(WasiBase):
    def execute(self, a: int, b: int) -> tuple[I32]:
        code = self.exec.memory[a : a + b].tobytes()
        model = to_model(code)

        block = self.exec.get_block(locals=[], stack=[])
        _ = block.run(model)

        stack = block.stack.all()
        print(f"execute: {code} -> {stack}")

        return WasiResult.SUCCESS


if __name__ == "__main__":
    with open("./assets/execute/target/wasm32-wasi/release/http_server.wasm", "rb") as f:
        wasm = f.read()

    assert set_logger()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    files = FS()

    env_ins = Env()
    env = WasiExportHelperUtil.export(env_ins, "env")
    ins = Wasi()
    export = WasiExportHelperUtil.export(ins, "wasi_snapshot_preview1")

    exec = WasmExec(optimizer, export + env)
    env_ins.init(exec)
    ins.init(exec=exec, fs=files)

    exec.start(b"_start", [])
    # exec.start(b"main", [])
