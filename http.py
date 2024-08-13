import logging
import os

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.wasi import WasiExportHelperUtil


def set_logger():
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
    with open("assets/hello_server.wasm", "rb") as f:
        wasm = f.read()

    assert set_logger()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    ins, export = WasiExportHelperUtil.export("wasi_snapshot_preview1")
    dummy = WasiExportHelperUtil.dummy(optimizer)

    exec = WasmExec(optimizer, export + dummy)
    ins.init(exec=exec)

    exec.start(b"_start", [])
    # exec.start(b"main", [])
