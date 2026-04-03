from __future__ import annotations


class WasmRiskEngine:
    """Optional WebAssembly scorer using wasmtime.

    If wasmtime is not available, adjust_score falls back to Python logic.
    """

    _WAT = r"""
    (module
      (func (export "adjust") (param $score i32) (param $issues i32) (result i32)
        local.get $score
        local.get $issues
        i32.const 3
        i32.mul
        i32.add))
    """

    def __init__(self) -> None:
        self._enabled = False
        self._adjust = None
        self._error = None

        try:
            import wasmtime  # type: ignore

            engine = wasmtime.Engine()
            module = wasmtime.Module(engine, self._WAT)
            store = wasmtime.Store(engine)
            instance = wasmtime.Instance(store, module, [])
            adjust = instance.exports(store)["adjust"]
            self._adjust = lambda score, issues: int(adjust(store, int(score), int(issues)))
            self._enabled = True
        except Exception as err:  # pragma: no cover - optional runtime
            self._error = str(err)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def error(self) -> str | None:
        return self._error

    def adjust_score(self, base_score: int, issues: int) -> int:
        if self._adjust:
            try:
                return self._adjust(base_score, issues)
            except Exception:
                pass
        return base_score + (issues * 2)
