# ADR 0011: Morph plans constrain presentation without creating state

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has exact execution traces, replayable Relic timelines, deterministic geometry scenes/deltas, and a reference SVG renderer. A browser or WebGL frontend needs more guidance than a raw geometry delta if it is going to present topology changes, translations, disappearance, persistence, or corpus-inspired visual behavior consistently.

Putting that decision logic directly in a frontend would create another source of undocumented semantics and would make different renderers disagree about what a transition means.

## Decision

TD-1 will define a versioned `td1.morph-plan` between exact geometry deltas and animation.

The morph plan will:

1. consume two exact `td1.geometry-scene` endpoints;
2. recompute and preserve their exact `td1.geometry-delta`;
3. map every changed primitive to a renderer-independent presentation intent;
4. preserve exact translation vectors for true move changes;
5. use conservative project-native fallbacks when no temporal corpus motif is admitted;
6. admit optional corpus-backed presentation hints only from a frozen geometry profile;
7. attach exact source IDs and stable rule IDs to every corpus-backed hint;
8. reject endpoint profile changes in v1 rather than presenting a corpus/configuration revision as machine motion;
9. remain silent on duration, easing, interpolation samples, camera behavior, audio, and intermediate machine state.

A companion `td1.timeline-morph-manifest` will contain exactly one morph plan for every noninitial `td1.relic-timeline` frame.

## Consequences

Positive:

- browser/WebGL renderers can share one transition-intent contract;
- corpus-inspired motion behavior becomes source-traceable rather than aesthetic folklore;
- topology changes have a conservative fallback when no morphing motif is admitted;
- true translations carry exact lattice displacement instead of requiring pixel inference;
- future temporal presentation experiments can be compared without changing machine semantics;
- a frontend can be visually expressive while remaining downstream of exact endpoint truth.

Costs:

- another versioned artifact must be maintained;
- early morph plans are intentionally conservative and may look abrupt until a player supplies presentation timing;
- mapping horizontal/vertical report motifs onto `q`/`r` lattice axes is explicitly a TD-1 engineering convention and must remain labeled as such;
- cross-profile transitions are deferred rather than guessed.

## Non-decision

This ADR does not define:

- animation duration;
- easing curves;
- intermediate geometry samples;
- frame rate;
- camera motion;
- persistence duration;
- audio;
- color animation;
- final art direction;
- physical display transport;
- physical instruction encoding.

Intermediate rendered pixels are not TD-1 machine state.