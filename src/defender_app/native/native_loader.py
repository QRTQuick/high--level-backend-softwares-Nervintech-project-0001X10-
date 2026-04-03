from __future__ import annotations

import ctypes
import platform
from pathlib import Path


class NativeLoadResult:
    def __init__(self) -> None:
        self.c_loaded = False
        self.cpp_loaded = False
        self.asm_loaded = False
        self.messages: list[str] = []

    def summary(self) -> str:
        return ", ".join(
            [
                f"C={'yes' if self.c_loaded else 'no'}",
                f"C++={'yes' if self.cpp_loaded else 'no'}",
                f"ASM={'yes' if self.asm_loaded else 'no'}",
            ]
        )


class NativeRiskEngine:
    def __init__(self) -> None:
        self._c_lib = None
        self._cpp_lib = None
        self._asm_lib = None
        self._result = NativeLoadResult()
        self._load_libraries()

    @property
    def load_result(self) -> NativeLoadResult:
        return self._result

    def _load_libraries(self) -> None:
        project_root = Path(__file__).resolve().parents[3]
        build_dir = project_root / "build" / "native"

        if platform.system().lower().startswith("win"):
            ext = ".dll"
        elif platform.system().lower() == "darwin":
            ext = ".dylib"
        else:
            ext = ".so"

        self._c_lib = self._load_lib(build_dir / f"libdefender_c{ext}", "c")
        self._cpp_lib = self._load_lib(build_dir / f"libdefender_cpp{ext}", "cpp")
        self._asm_lib = self._load_lib(build_dir / f"libdefender_asm{ext}", "asm")

        if self._c_lib:
            self._c_lib.c_risk_boost.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self._c_lib.c_risk_boost.restype = ctypes.c_int
            self._result.c_loaded = True

        if self._cpp_lib:
            self._cpp_lib.cpp_anomaly_signal.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self._cpp_lib.cpp_anomaly_signal.restype = ctypes.c_int
            self._result.cpp_loaded = True

        if self._asm_lib:
            self._asm_lib.asm_jitter.argtypes = [ctypes.c_uint64]
            self._asm_lib.asm_jitter.restype = ctypes.c_uint64
            self._result.asm_loaded = True

    def _load_lib(self, path: Path, label: str):
        if not path.exists():
            self._result.messages.append(f"{label}: missing {path.name}")
            return None
        try:
            return ctypes.CDLL(str(path))
        except OSError as err:
            self._result.messages.append(f"{label}: failed to load ({err})")
            return None

    def c_risk_boost(self, endpoint: str, issues: int) -> int:
        if self._c_lib:
            return int(self._c_lib.c_risk_boost(endpoint.encode("utf-8"), int(issues)))
        return (len(endpoint) % 5) + max(0, issues)

    def cpp_anomaly_signal(self, method: str, status_code: int | None) -> int:
        status = status_code if status_code is not None else 0
        if self._cpp_lib:
            return int(self._cpp_lib.cpp_anomaly_signal(method.encode("utf-8"), int(status)))
        score = 3 if status in (500, 502, 503, 504) else 0
        if method.upper() in {"PUT", "DELETE", "PATCH"}:
            score += 2
        return score

    def asm_jitter(self, seed: int) -> int:
        if self._asm_lib:
            value = int(self._asm_lib.asm_jitter(ctypes.c_uint64(seed)))
            return value & 0x7
        mixed = (seed ^ 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        mixed = ((mixed << 13) | (mixed >> (64 - 13))) & 0xFFFFFFFFFFFFFFFF
        return mixed & 0x7
