import logging
import os

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.wasi import Wasi, WasiExportHelperUtil


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


if __name__ == "__main__":
    # with open("websockets-doom.wasm", "rb") as f:
    with open("wasidoom2.wasm", "rb") as f:
        wasm = f.read()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    export = WasiExportHelperUtil.export(Wasi, "wasi_snapshot_preview1")
    dummy = WasiExportHelperUtil.dummy(optimizer)

    vm = WasmExec(optimizer, export + dummy)

    set_logger()
    vm.start(b"_start", [])
    # vm.start(b"main", [])
