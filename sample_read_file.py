import io
import logging
import os

import numpy as np

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.wasi import FS, Wasi, WasiExportHelperUtil


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


if __name__ == "__main__":
    with open("./assets/read_file.wasm", "rb") as f:
        wasm = f.read()

    assert set_logger()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    text = "Hello, World!"

    files = FS()

    files.mount("hello.txt", io.BytesIO(text.encode()))

    ins = Wasi()
    export = WasiExportHelperUtil.export(ins, "wasi_snapshot_preview1")

    exec = WasmExec(optimizer, export)
    ins.init(exec=exec, fs=files)

    exec.start(b"_start", [])
    # exec.start(b"main", [])
