# ADR 0012: Browser animation is presentation, not machine authority

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has deterministic contracts for logical execution, render state, native
geometry, geometry deltas, Relic timelines, and morph plans. The next useful
step is visible browser playback.

A browser animation system creates a new risk: convenient frontend code can
quietly become a second state machine. Pixel interpolation, layout heuristics,
or ad hoc motion could be mistaken for TD-1 activity even when no corresponding
logical event exists.

## Decision

The browser player is strictly downstream presentation software.

Authoritative TD-1 state exists only at exact validated `td1.relic-timeline`
frames. Browser animation may visually bridge adjacent endpoints only according
to validated `td1.morph-plan` descriptors.

The v1 player therefore follows these rules:

1. Exact canonical timeline and morph-manifest bytes are embedded in the
   standalone artifact and verified before playback.
2. Native geometry is rendered directly from `GeometryScene` primitives using
   the documented reference projection.
3. A primitive with no morph descriptor receives no transition animation.
4. A `translate` animation uses only the exact projected `(dq, dr, dz)` vector
   stored in the descriptor.
5. Enter, exit, reform, and retag behavior may alter presentation opacity or
   emphasis but may not create a new machine endpoint.
6. After every transition, the browser discards transient presentation state and
   reconstructs the exact authoritative target scene.
7. Timing, easing, persistence duration, glow, playback speed, autoplay, and
   looping are non-normative presentation configuration.
8. Corpus-backed hints can constrain presentation only when they are already
   present in a validated morph descriptor. The browser does not query or infer
   corpus evidence.

The manifest freezes the endpoint policy as:

```text
hard-reconcile-authoritative-scene-after-transition/v1
```

and freezes the interpolation policy as:

```text
forbidden/v1
```

for machine state.

## Consequences

The first player can be visually animated without becoming an alternate TD-1
simulator.

A frontend bug may temporarily display the wrong in-between picture, but the next
exact endpoint is rebuilt from authoritative geometry rather than accumulated
animation state.

This also makes future renderer replacement testable: SVG, DOM, Canvas, WebGL,
or a physical display may use different presentation techniques while consuming
the same timeline and morph contracts.

The cost is that some visually sophisticated effects are deferred until their
relationship to exact endpoint state is explicit.

## Rejected alternatives

### Let the browser diff SVG or pixels

Rejected because rendered pixels are downstream presentation and do not contain
sufficient normative information to distinguish real state change from renderer
choice.

### Let animation state become the next frame

Rejected because floating-point animation accumulation and browser-specific
behavior would become machine semantics.

### Generate arbitrary in-between geometry for every topology change

Rejected because a morph-plan eligibility hint does not define an interpolation
algorithm and does not create intermediate TD-1 states.

### Treat WebCrypto verification as authorship proof

Rejected. Embedded hashes provide integrity checks, not signatures or identity.
