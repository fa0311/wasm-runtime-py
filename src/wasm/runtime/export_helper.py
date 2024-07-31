from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import CodeSectionOptimize, TypeSectionOptimize, WasmSectionsOptimize
from src.wasm.runtime.export import WasmExport, WasmExportFunction
from src.wasm.type.numeric.base import NumericType


class ExportHelper:
    def __init__(self, sec: WasmSectionsOptimize, value: list[WasmExport]):
        self.sec = sec
        self.value = value

    def export(self, namespace: str, name: str, returns: list[NumericType]):
        def decorator(fn):
            annotations: list[NumericType] = [x for x in fn.__annotations__.values()]
            self.value.append(
                WasmExport(
                    namespace=namespace,
                    name=name,
                    data=WasmExportFunction(
                        type=TypeSectionOptimize(
                            form=0,
                            params=[WasmOptimizer.from_type(x) for x in annotations],
                            returns=[WasmOptimizer.from_type(x) for x in returns],
                        ),
                        code=CodeSectionOptimize(data=[], local=[]),
                        call=fn,
                    ),
                )
            )
            return fn

        return decorator
