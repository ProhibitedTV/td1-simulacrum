"""Binary-stream adapter for the TD-1 parity wire line-I/O boundary.

This module turns ordinary readable/writable binary streams into `ParityLineIO`.
It owns byte movement, buffering, progress checks, and adapter diagnostics only.
Canonical parity-wire semantics remain in `wire.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .wire import WIRE_MAX_FRAME_BYTES


class ParityStreamError(IOError):
    """Base class for concrete byte-stream adapter failures."""


class ParityStreamReadError(ParityStreamError):
    """Raised when the underlying reader fails or returns invalid data."""


class ParityStreamWriteError(ParityStreamError):
    """Raised when the underlying writer fails or cannot make progress."""


class ParityStreamEOFError(ParityStreamReadError):
    """Base class for EOF observed while waiting for a line frame."""


class ParityStreamEmptyEOFError(ParityStreamEOFError):
    """Raised when EOF arrives before any bytes of the next frame."""


class ParityStreamPartialEOFError(ParityStreamEOFError):
    """Raised when EOF arrives after an unterminated partial frame."""


class ParityStreamFrameTooLargeError(ParityStreamReadError):
    """Raised when an incoming line cannot fit inside the configured ceiling."""


class BinaryByteReader(Protocol):
    """Small readable-binary-stream surface used by `StreamParityLineIO`."""

    def read(self, size: int = -1) -> bytes: ...


class BinaryByteWriter(Protocol):
    """Small writable-binary-stream surface used by `StreamParityLineIO`."""

    def write(self, data: bytes) -> int | None: ...


class BinaryByteStream(BinaryByteReader, BinaryByteWriter, Protocol):
    """Minimal duplex binary stream suitable for serial/file/socket wrappers."""


@dataclass(frozen=True, slots=True)
class StreamParityStats:
    """Deterministic adapter counters with no wall-clock state."""

    bytes_read: int
    bytes_written: int
    frames_read: int
    frames_written: int
    buffered_bytes: int


class StreamParityLineIO:
    """Implement parity line I/O over ordinary binary streams.

    Pass either one duplex `stream`, or both an explicit `reader` and `writer`.
    Reads are buffered until one LF-terminated frame is available. Writes loop
    until every supplied byte has been accepted by the underlying writer.
    """

    def __init__(
        self,
        stream: BinaryByteStream | None = None,
        *,
        reader: BinaryByteReader | None = None,
        writer: BinaryByteWriter | None = None,
        max_frame_bytes: int = WIRE_MAX_FRAME_BYTES,
        read_chunk_bytes: int = 4096,
    ) -> None:
        if stream is not None:
            if reader is not None or writer is not None:
                raise ValueError("provide either stream or explicit reader/writer, not both")
            reader = stream
            writer = stream
        elif reader is None or writer is None:
            raise ValueError("explicit stream mode requires both reader and writer")
        if max_frame_bytes <= 1:
            raise ValueError("max_frame_bytes must allow payload plus newline")
        if read_chunk_bytes <= 0:
            raise ValueError("read_chunk_bytes must be positive")

        self._reader = reader
        self._writer = writer
        self._max_frame_bytes = max_frame_bytes
        self._read_chunk_bytes = read_chunk_bytes
        self._read_buffer = bytearray()
        self._bytes_read = 0
        self._bytes_written = 0
        self._frames_read = 0
        self._frames_written = 0

    @property
    def stats(self) -> StreamParityStats:
        return StreamParityStats(
            bytes_read=self._bytes_read,
            bytes_written=self._bytes_written,
            frames_read=self._frames_read,
            frames_written=self._frames_written,
            buffered_bytes=len(self._read_buffer),
        )

    @property
    def max_frame_bytes(self) -> int:
        return self._max_frame_bytes

    @property
    def read_chunk_bytes(self) -> int:
        return self._read_chunk_bytes

    def write_line(self, frame: bytes) -> None:
        if not isinstance(frame, bytes):
            raise ParityStreamWriteError("stream line frame must be bytes")
        if not frame:
            raise ParityStreamWriteError("stream line frame must not be empty")
        if len(frame) > self._max_frame_bytes:
            raise ParityStreamWriteError("outgoing stream line exceeds maximum frame size")

        offset = 0
        while offset < len(frame):
            remaining = frame[offset:]
            try:
                written = self._writer.write(remaining)
            except Exception as exc:
                raise ParityStreamWriteError("underlying stream write failed") from exc
            if type(written) is not int:
                raise ParityStreamWriteError("underlying stream write must return an integer")
            if written <= 0:
                raise ParityStreamWriteError("underlying stream write made zero progress")
            if written > len(remaining):
                raise ParityStreamWriteError("underlying stream write exceeded requested length")
            offset += written
            self._bytes_written += written

        flush = getattr(self._writer, "flush", None)
        if callable(flush):
            try:
                flush()
            except Exception as exc:
                raise ParityStreamWriteError("underlying stream flush failed") from exc
        self._frames_written += 1

    def _pop_buffered_frame(self) -> bytes | None:
        newline = self._read_buffer.find(b"\n")
        if newline < 0:
            if len(self._read_buffer) >= self._max_frame_bytes:
                raise ParityStreamFrameTooLargeError(
                    "unterminated stream line reached maximum frame size"
                )
            return None

        frame_length = newline + 1
        if frame_length > self._max_frame_bytes:
            raise ParityStreamFrameTooLargeError("incoming stream line exceeds maximum frame size")
        frame = bytes(self._read_buffer[:frame_length])
        del self._read_buffer[:frame_length]
        self._frames_read += 1
        return frame

    def read_line(self) -> bytes:
        while True:
            buffered = self._pop_buffered_frame()
            if buffered is not None:
                return buffered

            remaining_capacity = self._max_frame_bytes - len(self._read_buffer)
            request_size = min(self._read_chunk_bytes, max(1, remaining_capacity))
            try:
                chunk = self._reader.read(request_size)
            except Exception as exc:
                raise ParityStreamReadError("underlying stream read failed") from exc
            if not isinstance(chunk, bytes):
                raise ParityStreamReadError("underlying stream read must return bytes")
            if not chunk:
                if self._read_buffer:
                    raise ParityStreamPartialEOFError(
                        "stream ended with an unterminated partial frame"
                    )
                raise ParityStreamEmptyEOFError("stream ended before the next frame")

            self._read_buffer.extend(chunk)
            self._bytes_read += len(chunk)
