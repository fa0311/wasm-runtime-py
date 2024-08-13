import logging
import os

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.wasi import FS, Screen, Wasi, WasiExportHelperUtil


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
    with open("assets/wasidoom2.wasm", "rb") as f:
        wasm = f.read()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    screen = Screen.get_instance()

    f_doom = open("./assets/doom1.wad", "rb")

    files = FS.get_instance()
    files.mount("./doom1.wad", 5, f_doom, True)
    files.mount("./screen.data", 6, screen.f_scr, False)
    files.mount("./palette.raw", 7, screen.f_pal, False)

    export = WasiExportHelperUtil.export(Wasi, "wasi_snapshot_preview1")
    dummy = WasiExportHelperUtil.dummy(optimizer)

    vm = WasmExec(optimizer, export + dummy)

    assert set_logger()
    vm.start(b"_start", [])
    # vm.start(b"main", [])
