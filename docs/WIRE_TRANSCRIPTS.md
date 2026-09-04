# TD-1 Parity Wire Transcripts and Bench Runs

## Purpose

The parity wire can now be preserved as deterministic transport evidence.

A transcript records the **exact canonical line bytes** successfully written and read at the `ParityLineIO` boundary. It exists so a future hardware session can be inspected, fingerprinted, replayed without the original device, and linked back to the exact campaign/report that produced it.

It is not a second arithmetic authority and it is not proof that a particular physical board authored the bytes.

```text
ParityCampaign
      |
      v
run_conformance()
      |
      v
JsonLineParityTransport
      |
      v
RecordingParityLineIO ------> td1.parity-wire-transcript
      |
      v
real or reference line I/O
      |
      v
physical/reference target

campaign run + exact transcript
      |
      v
 td1.parity-bench-run
      |
      +------> verification
      |
      +------> ReplayParityLineIO
                       |
                       v
                normal wire transport
                       |
                       v
             identical campaign report
```

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

For the v0.16 reference path:

```text
JsonLineParityTransport
        |
        v
RecordingParityLineIO
        |
        v
InMemoryParityLineIO
        |
        v
ParityWireDevice
        |
        v
ReferenceLoopbackTransport
```

The same recording wrapper can later sit above a serial line implementation without changing the artifact schema.

## Replay

`ReplayParityLineIO` consumes a validated transcript.

Host writes must match the next recorded `host_to_device` frame **byte for byte**. Reads return the exact saved device-response bytes.

Replay rejects:

- read before the required host write;
- a second host write before the response is consumed;
- request bytes that differ from the transcript;
- traffic after transcript end;
- incomplete transcript consumption.

This means replay is not a loose mock. It is a deterministic byte-level reproduction of one recorded wire conversation.

## Reconstructing expected traffic from a report

`transcript_for_report()` deterministically regenerates the canonical wire traffic implied by a `td1.parity-report`:

1. capability request;
2. capability response containing the exact saved capabilities;
3. one parity request/response pair for each vector the advertised capabilities accepted.

Vectors rejected by capability negotiation never reach `ParityTransport.exchange()` and therefore correctly produce no parity wire pair.

This distinction matters: an `unsupported` report record synthesized by host capability gating is report truth, but it was not device wire traffic.

## Bench-run bundle

`td1.parity-bench-run` binds:

- one exact `td1.parity-campaign-run`;
- one exact `td1.parity-wire-transcript`.

The bundle validates the transcript by reconstructing the expected wire traffic from the saved conformance report and requiring canonical equality.

Because `ParityCampaignRun` already binds the report to the exact campaign and ordered vectors, the bench bundle creates this provenance chain:

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

A transcript cannot be substituted from a different target, session, vector sequence, response set, or telemetry set without invalidating the bench bundle.

## Deterministic replay verification

`replay_bench_run()` creates a normal `JsonLineParityTransport` over `ReplayParityLineIO`, reruns the saved campaign with the saved session ID, and requires the resulting canonical `ParityCampaignRun` to equal the saved campaign run exactly.

The replay therefore passes through the same capability negotiation and response parsing used by live wire execution.

## CLI

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

Verify the complete bench bundle and replay it through the normal wire transport:

```bash
td1-parity bench-run-replay sum.bench.json
```

## What a transcript proves

A valid transcript proves that:

- every saved frame is valid canonical v1 wire data;
- frame bytes match their saved SHA-256;
- decoded kind/correlation metadata matches the bytes;
- request/response ordering is legal;
- a replay consumer can reproduce the same byte conversation.

A valid bench run additionally proves that the saved transcript is exactly the wire conversation implied by its saved campaign report.

It does **not** by itself prove:

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
