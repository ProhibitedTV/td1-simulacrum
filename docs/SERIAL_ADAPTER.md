# Optional Serial Live-Bench Adapter

## Purpose

v0.18 adds the first optional host deployment path capable of opening a real serial port and running an existing TD-1 parity campaign through the same stream, wire, transcript, and bench-run contracts already exercised in CI.

```text
saved td1.parity-campaign
          |
          v
 JsonLineParityTransport
          |
          v
 RecordingParityLineIO
          |
          v
   StreamParityLineIO
          |
          v
   PySerialByteStream
          |
          v
      pyserial
          |
          v
 UART / USB CDC device
```

Serial deployment details remain below TD-1 semantics. Port names, baud rate, and host timeout values are runtime settings rather than machine-state, parity, wire, transcript, or bench-run fields.

## Optional dependency

Core installs do not require pyserial.

Install the live serial extra only on hosts that need it:

```bash
python -m pip install -e '.[serial]'
```

Development/test installs remain able to exercise the adapter with injected fake serial modules and ports. CI therefore does not require a physical device or a pyserial installation merely to validate the core package.

## Explicit configuration

`SerialConfig` requires four explicit host settings:

- `port`;
- `baudrate`;
- `read_timeout_s`;
- `write_timeout_s`.

All values are validated before opening the port. Baud rate must be a positive integer. Timeouts must be positive finite numbers.

These values are deployment diagnostics only. They are not automatically copied into canonical parity artifacts.

No default baud rate is selected by TD-1.

## PySerialByteStream

`PySerialByteStream` wraps a pyserial-compatible port and presents the generic binary read/write/flush/close behavior expected by `StreamParityLineIO`.

It deliberately does **not** implement line buffering or JSON framing. Those responsibilities remain in the layers that already own them:

```text
pyserial bytes
    -> PySerialByteStream
      -> StreamParityLineIO
        -> complete LF-terminated frames
          -> JsonLineParityTransport
            -> canonical td1.parity-wire semantics
```

## Timeout behavior

A live serial session uses finite positive read and write timeouts.

For that reason, a zero-byte pyserial read is interpreted as **serial read timeout**, not EOF.

The adapter exposes explicit diagnostics:

- `ParitySerialReadTimeoutError`;
- `ParitySerialWriteTimeoutError`;
- `ParitySerialReadError`;
- `ParitySerialWriteError`;
- `ParitySerialClosedError`;
- `ParitySerialCloseError`;
- `ParitySerialDependencyError`.

`StreamParityLineIO` preserves adapter-specific `ParityStreamError` subclasses rather than collapsing them into generic read/write wrapper errors.

These exceptions are host adapter diagnostics. They are not `ParityStatus` values returned by a TD-1 target.

## Resource ownership

`PySerialByteStream` is a context manager.

```python
with open_pyserial_stream(config) as stream:
    line_io = StreamParityLineIO(stream)
```

Normal exit closes the port exactly once. Explicit repeated `close()` calls are idempotent after a successful close.

Use after close is rejected.

## Live CLI

`td1-parity serial-run` executes a saved parity campaign against an explicitly configured live port:

```bash
td1-parity serial-run sum.campaign.json \
  --port /dev/ttyACM0 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --output sum.serial.run.json \
  --transcript-output sum.serial.transcript.json \
  --bench-output sum.serial.bench.json
```

Windows example:

```bash
td1-parity serial-run sum.campaign.json \
  --port COM7 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --output sum.serial.run.json
```

The command requires explicit `--port`, `--baud`, `--read-timeout`, and `--write-timeout` values.

The normal output artifacts remain unchanged:

- `td1.parity-campaign-run`;
- optional `td1.parity-wire-transcript`;
- optional `td1.parity-bench-run`.

The CLI summary may additionally show serial deployment settings and deterministic `StreamParityStats`. Those summary fields are not embedded into the normative artifacts.

## Evidence boundary

A successful `serial-run` means the host successfully:

1. opened the configured serial port;
2. exchanged canonical TD-1 parity-wire frames;
3. received responses that passed the existing parity evaluation;
4. optionally preserved the exact wire conversation and linked bench bundle.

It does not by itself prove:

- the electrical quality of a trit level;
- comparator threshold margin;
- signal integrity;
- hardware authorship or device identity;
- instruction fetch/decode;
- physical instruction encoding.

Those claims require the corresponding measured telemetry, lab evidence, or future authenticated/physical contracts.

## Non-goals

v0.18 does not:

- auto-discover serial ports;
- select a default baud rate;
- define USB VID/PID;
- define connector/pinout;
- define retry/reconnect policy;
- define electrical thresholds;
- define measured acceptance criteria;
- add wall-clock timestamps to normative artifacts;
- freeze Issue #2 physical instruction encoding.

## Design rule

**Open a real byte link without letting deployment configuration become machine truth.**
