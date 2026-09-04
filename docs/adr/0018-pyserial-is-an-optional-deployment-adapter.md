# ADR 0018 — Pyserial is an optional deployment adapter

- Status: Accepted
- Revision: v0.18

## Context

TD-1 now has:

- transport-neutral parity contracts;
- canonical `td1.parity-wire` framing;
- deterministic wire transcripts and bench-run replay;
- `StreamParityLineIO` over ordinary binary streams.

The remaining host-side gap for a first UART/USB-CDC bench target is opening an operating-system serial port.

That gap is a deployment concern, not a reason to make one serial library, baud rate, port name, timeout, USB identity, or connector part of TD-1 machine semantics.

## Decision

Pyserial is introduced only as an optional package extra and runtime adapter.

The dependency is loaded lazily when live serial operation is requested.

A configured pyserial port is wrapped by `PySerialByteStream`, which satisfies the binary stream surface consumed by `StreamParityLineIO`.

The complete live stack remains:

```text
ParityCampaign
    -> JsonLineParityTransport
      -> RecordingParityLineIO
        -> StreamParityLineIO
          -> PySerialByteStream
            -> pyserial
              -> physical serial link
```

The existing layers retain their authority:

- `ParityTransport` owns parity request/response semantics;
- `td1.parity-wire` owns canonical frame semantics;
- `StreamParityLineIO` owns line buffering and byte progress;
- `PySerialByteStream` owns serial-specific open/read/write/timeout/close behavior;
- transcripts preserve exact completed wire frames;
- deployment settings remain outside normative artifacts.

`td1-parity serial-run` requires explicit port, baud rate, read timeout, and write timeout values.

No default baud rate is defined by the project.

## Timeout interpretation

Finite positive serial timeouts are required for the live adapter.

A zero-byte pyserial read is therefore classified as serial read timeout rather than generic EOF.

Serial-specific timeout/error classes derive from the stream adapter error hierarchy and are preserved through `StreamParityLineIO`.

They remain host adapter diagnostics rather than target `ParityStatus` values.

## Artifact policy

The normal live-run artifacts remain unchanged:

- `td1.parity-campaign-run`;
- `td1.parity-wire-transcript`;
- `td1.parity-bench-run`.

Port name, baud rate, and host timeout settings may appear in a human/CLI execution summary, but are not automatically embedded in those canonical artifacts.

This keeps replay and parity truth independent from the host machine used to reach the device.

## Consequences

### Positive

- first real serial-class hardware can be reached without changing parity or wire schemas;
- core installations remain dependency-free;
- CI can test the live path with injected fake serial modules and no physical device;
- serial timeout and close behavior becomes explicit;
- existing transcript/bench evidence remains reusable unchanged.

### Negative

- live serial use requires installing an optional extra;
- operators must provide deployment settings explicitly;
- reconnect/discovery policy remains outside the current adapter;
- a successful serial exchange still does not establish electrical quality or hardware identity.

## Deferred

This ADR does not define:

- port auto-discovery;
- default baud rate;
- USB VID/PID;
- connector/pinout;
- retry/reconnect policy;
- electrical acceptance limits;
- authenticated hardware identity;
- physical instruction encoding.

## Rule

**A serial library may carry TD-1 bytes; it does not get to define TD-1.**
