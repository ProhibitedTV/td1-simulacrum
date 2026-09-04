"""Optional pyserial deployment adapter for TD-1 parity bench sessions.

This module opens a configured serial port and exposes it as a binary stream for
`StreamParityLineIO`. Serial configuration is deployment state only; it does not
enter TD-1 parity, wire, transcript, or machine-state semantics.
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from types import ModuleType
from typing import Protocol

from .stream_io import (
    ParityStreamError,
    ParityStreamReadError,
    ParityStreamWriteError,
)


class ParitySerialError(ParityStreamError):
    """Base class for optional serial-adapter failures."""


class ParitySerialDependencyError(ParitySerialError):
    """Raised when live serial use is requested without the optional dependency."""


class ParitySerialClosedError(ParitySerialError):
    """Raised when a closed serial stream is used."""


class ParitySerialReadTimeoutError(ParityStreamReadError, ParitySerialError):
    """Raised when a configured serial read times out before any bytes arrive."""


class ParitySerialWriteTimeoutError(ParityStreamWriteError, ParitySerialError):
    """Raised when pyserial reports a write timeout."""


class ParitySerialReadError(ParityStreamReadError, ParitySerialError):
    """Raised for underlying serial read failures."""


class ParitySerialWriteError(ParityStreamWriteError, ParitySerialError):
    """Raised for underlying serial write or flush failures."""


class ParitySerialCloseError(ParitySerialError):
    """Raised when releasing the serial port fails."""


@dataclass(frozen=True, slots=True)
class SerialConfig:
    """Explicit host deployment settings for one live serial bench session."""

    port: str
    baudrate: int
    read_timeout_s: float
    write_timeout_s: float

    def __post_init__(self) -> None:
        if not isinstance(self.port, str) or not self.port.strip():
            raise ValueError("serial port must not be empty")
        if type(self.baudrate) is not int or self.baudrate <= 0:
            raise ValueError("serial baudrate must be a positive integer")
        if not _positive_finite_number(self.read_timeout_s):
            raise ValueError("serial read_timeout_s must be a positive finite number")
        if not _positive_finite_number(self.write_timeout_s):
            raise ValueError("serial write_timeout_s must be a positive finite number")

    def as_dict(self) -> dict[str, object]:
        """Return deployment settings for non-normative CLI diagnostics."""
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "read_timeout_s": self.read_timeout_s,
            "write_timeout_s": self.write_timeout_s,
        }


def _positive_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value > 0 and math.isfinite(float(value))


class SerialPortLike(Protocol):
    """Small pyserial-compatible object surface wrapped by `PySerialByteStream`."""

    is_open: bool

    def read(self, size: int = -1) -> bytes: ...

    def write(self, data: bytes) -> int | None: ...

    def flush(self) -> None: ...

    def close(self) -> None: ...


class PySerialByteStream:
    """Translate pyserial behavior into the generic binary stream contract.

    A finite positive read timeout is required by `SerialConfig`, so a zero-byte
    pyserial read means timeout rather than EOF. `StreamParityLineIO` remains
    responsible for line buffering and maximum-frame enforcement.
    """

    def __init__(
        self,
        serial_port: SerialPortLike,
        *,
        serial_exception: type[BaseException],
        serial_timeout_exception: type[BaseException],
    ) -> None:
        self._serial_port = serial_port
        self._serial_exception = serial_exception
        self._serial_timeout_exception = serial_timeout_exception
        self._closed = False

    @property
    def is_open(self) -> bool:
        return not self._closed and bool(getattr(self._serial_port, "is_open", True))

    def _require_open(self) -> None:
        if not self.is_open:
            raise ParitySerialClosedError("serial stream is closed")

    def read(self, size: int = -1) -> bytes:
        self._require_open()
        try:
            chunk = self._serial_port.read(size)
        except self._serial_timeout_exception as exc:
            raise ParitySerialReadTimeoutError("serial read timed out") from exc
        except self._serial_exception as exc:
            raise ParitySerialReadError("underlying serial read failed") from exc
        if chunk == b"":
            raise ParitySerialReadTimeoutError("serial read timed out")
        return chunk

    def write(self, data: bytes) -> int | None:
        self._require_open()
        try:
            return self._serial_port.write(data)
        except self._serial_timeout_exception as exc:
            raise ParitySerialWriteTimeoutError("serial write timed out") from exc
        except self._serial_exception as exc:
            raise ParitySerialWriteError("underlying serial write failed") from exc

    def flush(self) -> None:
        self._require_open()
        try:
            self._serial_port.flush()
        except self._serial_timeout_exception as exc:
            raise ParitySerialWriteTimeoutError("serial flush timed out") from exc
        except self._serial_exception as exc:
            raise ParitySerialWriteError("underlying serial flush failed") from exc

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._serial_port.close()
        except self._serial_exception as exc:
            raise ParitySerialCloseError("underlying serial close failed") from exc
        self._closed = True

    def __enter__(self) -> "PySerialByteStream":
        self._require_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False


def _load_pyserial() -> ModuleType:
    try:
        return importlib.import_module("serial")
    except ModuleNotFoundError as exc:
        raise ParitySerialDependencyError(
            "pyserial is not installed; install td1-simulacrum[serial] for serial-run"
        ) from exc


def open_pyserial_stream(
    config: SerialConfig,
    *,
    serial_module: ModuleType | object | None = None,
) -> PySerialByteStream:
    """Open one configured serial port and return the generic binary-stream wrapper."""
    module = _load_pyserial() if serial_module is None else serial_module
    try:
        serial_factory = module.Serial
        serial_exception = module.SerialException
        serial_timeout_exception = module.SerialTimeoutException
    except AttributeError as exc:
        raise ParitySerialDependencyError(
            "pyserial module is missing required API members"
        ) from exc

    try:
        port = serial_factory(
            port=config.port,
            baudrate=config.baudrate,
            timeout=config.read_timeout_s,
            write_timeout=config.write_timeout_s,
        )
    except serial_timeout_exception as exc:
        raise ParitySerialWriteTimeoutError("serial port open timed out") from exc
    except serial_exception as exc:
        raise ParitySerialError("serial port open failed") from exc

    return PySerialByteStream(
        port,
        serial_exception=serial_exception,
        serial_timeout_exception=serial_timeout_exception,
    )
