import io
import logging
import sys
from typing import Callable

from src.tools.logger import NestedLogger
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import CodeSectionOptimize, TypeSectionOptimize, WasmSectionsOptimize
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.export import WasmExport, WasmExportFunction
from src.wasm.type.base import AnyType
from src.wasm.type.numeric.base import NumericType
from src.wasm.type.numeric.numpy.int import I32


class WasiResult:
    SUCCESS = (I32.from_int(0),)
    BADF = (I32.from_int(8),)


class FileType:
    DIR = 3
    REG = 4


class WasiExportHelperUtil:
    logger = NestedLogger(logging.getLogger(__name__))

    @classmethod
    def export(cls, clss: type, namespace: str) -> list[WasmExport]:
        value = clss.__dict__.values()
        ins = clss()
        data: list[WasmExport] = []
        for v in value:
            if isinstance(v, Callable):
                ignore = ["env", "return"]
                annotations: list[NumericType] = [v for k, v in v.__annotations__.items() if k not in ignore]
                ret = [v for k, v in v.__annotations__.items() if k == "return"]

                returns: list[NumericType] = ret[0].__args__ if ret else []

                def call(env: WasmExec, args: list[AnyType], ins=ins, name=v.__name__):
                    WasiExportHelperUtil.logger.debug(f"call: {name}")
                    return getattr(ins, name)(env, *args) or []

                data.append(
                    WasmExport(
                        namespace=namespace,
                        name=v.__name__,
                        data=WasmExportFunction(
                            type=TypeSectionOptimize(
                                form=0,
                                params=[WasmOptimizer.from_type(x) for x in annotations],
                                returns=[WasmOptimizer.from_type(x) for x in returns],
                            ),
                            code=CodeSectionOptimize(data=[], local=[]),
                            call=call,
                        ),
                    )
                )

        return data

    @classmethod
    def dummy(cls, opt: WasmSectionsOptimize) -> list[WasmExport]:
        data: list[WasmExport] = []
        for a in opt.import_section:
            data.append(
                WasmExport(
                    namespace=a.module.data.decode(),
                    name=a.name.data.decode(),
                    data=WasmExportFunction(
                        type=TypeSectionOptimize(form=0, params=[], returns=[]),
                        code=CodeSectionOptimize(data=[], local=[]),
                        call=lambda env, x: [],
                    ),
                )
            )
        return data


WAD = "mount/doom1.wad"
f_doom = open(WAD, "rb")
f_scr = io.BytesIO()
f_pal = io.BytesIO()


def stdout_write(data):
    sys.stdout.buffer.write(data)


vfs = {
    "<stdin>": {
        "fd": 0,
        "type": FileType.REG,
    },
    "<stdout>": {"fd": 1, "type": FileType.REG, "write": stdout_write},
    "<stderr>": {"fd": 2, "type": FileType.REG, "write": stdout_write},
    "/": {"fd": 3, "type": FileType.DIR, "dirname": b"/\x00"},
    "./doom1.wad": {"fd": 5, "type": FileType.REG, "file": f_doom, "exists": True},
    "./screen.data": {"fd": 6, "type": FileType.REG, "file": f_scr, "exists": False},
    "./palette.raw": {"fd": 7, "type": FileType.REG, "file": f_pal, "exists": False},
}
vfs_fds = {v["fd"]: v for (k, v) in vfs.items()}


class Wasi:
    def proc_exit(self, env: WasmExec, a: I32):
        sys.exit(int(a))

    def clock_time_get(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        raise Exception("not implemented")

    def fd_filestat_get(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")

    def poll_oneoff(self, env: WasmExec, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def fd_write(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        data = b""
        if int(a) == 2:
            for i in range(int(c)):
                iov = int(b) + 8 * i
                off = I32.from_bits(env.memory[iov : iov + 4])
                size = I32.from_bits(env.memory[iov + 4 : iov + 8])
                data += env.memory[int(off) : int(off) + int(size)].tobytes()

            print(data.decode(), end="")
            return WasiResult.SUCCESS

        raise Exception("invalid fd")

    def fd_read(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        raise Exception("not implemented")

    def fd_close(self, env: WasmExec, a: I32):
        raise Exception("not implemented")

    def fd_seek(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        raise Exception("not implemented")

    def fd_prestat_get(self, env: WasmExec, a: I32, b: I32) -> tuple[I32]:
        if int(a) != 3:
            return WasiResult.BADF

        name_len = len(vfs_fds[int(a)]["dirname"])
        env.memory[int(b) : int(b) + 4] = I32.from_int(0).to_bytes()[0:4]
        env.memory[int(b) + 4 : int(b) + 8] = I32.from_int(name_len).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def fd_prestat_dir_name(self, env: WasmExec, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def fd_fdstat_get(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")

    def path_open(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32, e: I32, f: I32):
        raise Exception("not implemented")

    def path_filestat_get(self, env: WasmExec, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def path_create_directory(self, env: WasmExec, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def args_sizes_get(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")

        env.memory[int(a) : int(a) + 4] = I32.from_int(3).to_bytes()[0:4]
        env.memory[int(b) : int(b) + 4] = I32.from_int(32).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def args_get(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")

        env.memory[int(a) : int(a) + 4] = b.to_bytes()[0:4]
        env.memory.store(int(b), b"doom\0")

        return WasiResult.SUCCESS

    def environ_sizes_get(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")

    def environ_get(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")

    def fd_fdstat_set_flags(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")
