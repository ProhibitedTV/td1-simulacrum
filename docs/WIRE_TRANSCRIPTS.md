# TD-1 Parity Wire Transcripts and Evidence

## Purpose

The parity wire can be preserved as deterministic transport evidence.

A transcript records the **exact canonical line bytes** successfully written and read at the `ParityLineIO` boundary. It exists so a future hardware session can be inspected, fingerprinted, replayed without the original device, and linked back to the exact conformance result that produced it.

It is not a second arithmetic authority and it is not proof that a particular physical board authored the bytes.

v0.19 supports two evidence roots over the same transcript contract:

```text
any td1.parity-report + exact transcript
        -> td1.parity-wire-evidence

trace-derived td1.parity-campaign-run + exact transcript
        -> td1.parity-bench-run
```

The campaign-specific bench bundle keeps its v1 schema. Both artifact families use the same deterministic report-to-transcript reconstruction rule.

## Transcript schema

Wire transcript v1 uses:

```text
schema  = td1.parity-wire-transcript
version = 1
```

Each ordered record preserves:

- contiguous `ordinal`;
- direction: `host_to_device` or `device_to_host`;
- exact canonical UTF-8 frame text including the trailing LF;
- SHA-256 of the exact frame bytes;
- decoded wire message kind;
- correlation ID;
- deterministic envelope digest.

Every record is validated by the existing `decode_wire_frame()` implementation. A transcript therefore cannot make malformed or noncanonical traffic look valid merely by storing metadata beside it.

## Ordering contract

A completed transcript is a sequence of complete line exchanges:

```text
host_to_device request
        ↓
device_to_host response
        ↓
host_to_device request
        ↓
device_to_host response
        ...
```

Ordinals must be contiguous from zero. The transcript must end after a device response.

Request/response message classes must match:

- `capabilities_request` -> `capabilities_response`;
- `parity_request` -> `parity_response`.

The response correlation ID must equal the corresponding request correlation ID.

No wall-clock timestamp is part of the normative v1 schema. Real timing remains optional device telemetry until a separate measured timing contract exists.

## Recording

`RecordingParityLineIO` wraps any existing `ParityLineIO`.

It preserves successful traffic without changing the underlying wire semantics:

1. validate canonical host frame;
2. delegate `write_line()`;
3. record exact host bytes;
4. delegate `read_line()`;
5. validate canonical device frame;
6. record exact device bytes.

The wrapper enforces write/read alternation. A transcript cannot be finalized while a device response is still unread.

## Stream and serial composition

The recording layer sits above byte-stream transport:

```text
JsonLineParityTransport
        |
        v
RecordingParityLineIO
        |
        v
StreamParityLineIO
        |
        v
PySerialByteStream / other binary stream
        |
        v
physical/reference target
```

That placement matters. Transcript v1 records the same canonical line frames regardless of whether the lower channel is in-memory, fragmented, coalesced, UART-backed, USB-backed, or another compatible stream. No transcript schema change is needed merely because the host begins talking to real serial-class hardware.

`StreamParityLineIO` may split writes or reassemble fragmented reads internally, but the recorder sees only complete canonical line operations. Its deterministic byte/frame counters are adapter diagnostics, not transcript fields or machine state.

## Reconstructing expected traffic from a report

`transcript_for_report()` deterministically regenerates the canonical wire traffic implied by any `td1.parity-report`:

1. capability request;
2. capability response containing the exact saved capabilities;
3. one parity request/response pair for each vector the advertised capabilities accepted.

Vectors rejected by capability negotiation never reach `ParityTransport.exchange()` and therefore correctly produce no parity wire pair.

This distinction matters: an `unsupported` report record synthesized by host capability gating is report truth, but it was not device wire traffic.

`validate_report_transcript()` is the shared linkage rule used by both generic wire evidence and campaign-specific bench runs. It reconstructs the expected transcript and requires canonical equality.

That rejects substitution of a different:

- target capability advertisement;
- session;
- vector order or operands;
- response status or observed value;
- telemetry payload;
- canonical wire frame.

## Generic wire-evidence bundle

v0.19 introduces:

```text
schema  = td1.parity-wire-evidence
version = 1
```

`ParityWireEvidence` binds:

- one exact `td1.parity-report`;
- one exact `td1.parity-wire-transcript`.

Unlike `td1.parity-bench-run`, it does not require a trace-derived campaign. This is important for fixed first-hardware suites such as the three one-trit `trit_hold` vectors used by TRIT_CELL_REV0 bring-up.

The artifact stores report and transcript digests for integrity and reconstructs the complete expected wire conversation during validation.

## Generic evidence replay

`replay_wire_evidence()` creates a normal `JsonLineParityTransport` over `ReplayParityLineIO`, reruns the exact saved request vectors with the exact saved session ID, requires complete transcript consumption, and requires the regenerated canonical `td1.parity-report` to equal the saved report.

This is a deterministic replay of one conformance conversation, not a permissive mock.

CLI:

```bash
td1-parity wire-evidence-verify trit.evidence.json

td1-parity wire-evidence-replay trit.evidence.json
```

## Campaign-specific bench-run bundle

`td1.parity-bench-run` still binds:

- one exact `td1.parity-campaign-run`;
- one exact `td1.parity-wire-transcript`.

The v1 schema is unchanged.

Because `ParityCampaignRun` already binds the report to the exact trace-derived campaign and ordered vectors, the bench bundle creates this provenance chain:

```text
logical execution trace
    -> parity campaign
      -> parity requests
        -> exact recorded wire frames
          -> parity responses
            -> conformance report
              -> campaign run
                -> bench run
```

The bench artifact now reuses the same report/transcript validation rule as generic wire evidence rather than maintaining a different interpretation of what the report implies on the wire.

## Bench replay

`replay_bench_run()` creates a normal `JsonLineParityTransport` over `ReplayParityLineIO`, reruns the saved campaign with the saved session ID, and requires the resulting canonical `ParityCampaignRun` to equal the saved campaign run exactly.

CLI:

```bash
td1-parity bench-run-replay sum.bench.json
```

## First-hardware evidence

The first one-trit serial session should use fixed golden vectors rather than manufacturing trace provenance:

```bash
td1-parity serial-golden \
  --suite trit \
  --port /dev/ttyACM0 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --report-output trit.report.json \
  --transcript-output trit.transcript.json \
  --evidence-output trit.evidence.json
```

For a target advertising only `trit_hold`, width 1, the transcript contains exactly four exchanges: one capability exchange and three parity exchanges.

See [`FIRST_HARDWARE_GOLDEN.md`](FIRST_HARDWARE_GOLDEN.md) and ADR 0019.

## Existing campaign recording CLI

Record a normal wire-loopback campaign plus transport evidence:

```bash
td1-parity wire-loopback sum.campaign.json \
  --output sum.wire.run.json \
  --transcript-output sum.wire.transcript.json \
  --bench-output sum.bench.json
```

Verify a saved transcript independently:

```bash
td1-parity wire-transcript-verify sum.wire.transcript.json
```

## What a transcript proves

A valid transcript proves that:

- every saved frame is valid canonical v1 wire data;
- frame bytes match their saved SHA-256;
- decoded kind/correlation metadata matches the bytes;
- request/response ordering is legal;
- a replay consumer can reproduce the same byte conversation.

A valid generic wire-evidence artifact additionally proves that the transcript is exactly the wire conversation implied by the saved conformance report.

A valid bench run additionally binds that same report/transcript relationship to one exact trace-derived campaign run.

None of these artifacts by themselves prove:

- which physical device generated the response;
- that a physical device was attached at all;
- analog voltage quality;
- timing quality;
- calibration quality;
- instruction fetch/decode;
- physical instruction encoding.

When real hardware arrives, board identity and measurements can be carried as report telemetry and supported by external lab records. Cryptographic device attestation, if ever desired, would require a separate authenticated protocol rather than pretending SHA-256 integrity hashes are signatures.

## Design rule

**Record exact transport evidence without promoting transport evidence into machine truth.**
