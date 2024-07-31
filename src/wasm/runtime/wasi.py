from typing import Callable

from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import CodeSectionOptimize, TypeSectionOptimize
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


fs = {
    "<stdin>": {"fd": 0, "type": FileType.REG},
    "<stdout>": {"fd": 1, "type": FileType.REG},
    "<stderr>": {"fd": 2, "type": FileType.REG},
    "/": {"fd": 3, "type": FileType.DIR, "dirname": b"/\x00"},
}


class WasiExportHelperUtil:
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
                    ins.logger.debug(f"call: {name}")
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


class Wasi:
    logger = WasmExec.logger

    def proc_exit(self, env: WasmExec, a: I32):
        pass

    def clock_time_get(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        pass

    def fd_filestat_get(self, env: WasmExec, a: I32, b: I32):
        pass

    def poll_oneoff(self, env: WasmExec, a: I32, b: I32, c: I32):
        pass

    def fd_write(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        pass

    def fd_read(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        pass

    def fd_close(self, env: WasmExec, a: I32):
        pass

    def fd_seek(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32):
        pass

    def fd_prestat_get(self, env: WasmExec, a: I32, b: I32) -> tuple[I32]:
        if a.value != 3:
            return WasiResult.BADF

        env.memory.store(offset=int(b.value), value=fs["/"]["dirname"])

        return WasiResult.SUCCESS

    def fd_prestat_dir_name(self, env: WasmExec, a: I32, b: I32, c: I32):
        pass

    def fd_fdstat_get(self, env: WasmExec, a: I32, b: I32):
        pass

    def path_open(self, env: WasmExec, a: I32, b: I32, c: I32, d: I32, e: I32, f: I32):
        pass

    def path_filestat_get(self, env: WasmExec, a: I32, b: I32, c: I32):
        pass

    def path_create_directory(self, env: WasmExec, a: I32, b: I32, c: I32):
        pass

    def args_sizes_get(self, env: WasmExec, a: I32, b: I32):
        pass

    def args_get(self, env: WasmExec, a: I32, b: I32):
        pass

    def environ_sizes_get(self, env: WasmExec, a: I32, b: I32):
        pass

    def environ_get(self, env: WasmExec, a: I32, b: I32):
        pass

    def fd_fdstat_set_flags(self, env: WasmExec, a: I32, b: I32):
        pass
