# ADR 0008: Hardware earns authority through transport-neutral parity

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 is intended to migrate from a software reference model into physical balanced-ternary subsystems. The project needs a rule for when a physical implementation is allowed to replace an emulated one.

If each board invents its own ad-hoc test script or transport framing, conformance becomes tied to bench setup rather than machine semantics. If physical hardware is treated as authoritative merely because it exists, semantic bugs can be promoted into the reference architecture.

The first planned hardware is much smaller than a full computer: one physical trit cell and then a register slice.

## Decision

TD-1 will use a transport-neutral parity protocol and deterministic golden vectors before any physical subsystem can replace its emulated counterpart.

The v1 parity layer defines:

- capability negotiation;
- versioned request and response records;
- deterministic ternary slice-state digests;
- register and ALU golden vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` statuses;
- replayable conformance reports containing every request, response, pass/fail decision, and discrepancy;
- a reference loopback target that proves the host harness before hardware is attached.

Physical transports are implemented as adapters exposing the same host-side interface. UART, USB, GPIO, Ethernet, or another link may be chosen later without changing logical conformance semantics.

The first physical target will advertise only the capabilities it has actually demonstrated. A one-trit board should begin with `trit_hold`, `max_width=1` and earn wider/register/ALU capabilities incrementally.

## Consequences

Positive:

- physical hardware can be compared against one deterministic oracle;
- transport choice does not redefine machine semantics;
- unsupported capabilities are distinguished from failed tests;
- bench failures retain exact vector identity and fault category;
- conformance logs are reproducible and reviewable;
- the first trit-cell experiment has a direct path into the emulator architecture;
- later register and ALU boards can reuse the same harness.

Costs:

- every hardware adapter must implement capability advertisement and request/response translation;
- bench integration includes more structured metadata than an ad-hoc script;
- physical implementations cannot claim broad capability before vectors pass;
- analog timing/calibration still require a separate hardware-specific contract.

## Non-decision

This ADR does not choose a physical transport, define voltage thresholds, sample timing, calibration, connector pinout, full-machine replacement, cycle timing, or physical instruction encoding.
