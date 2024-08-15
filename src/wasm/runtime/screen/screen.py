import sys

if "pypy" in sys.executable:
    import pypyjit  # type: ignore # noqa

    from src.wasm.runtime.screen.pypy import Screen  # type: ignore # noqa

    pypyjit.set_param("max_unroll_recursion=-1")
else:
    from src.wasm.runtime.screen.cpython import Screen  # type: ignore # noqa
