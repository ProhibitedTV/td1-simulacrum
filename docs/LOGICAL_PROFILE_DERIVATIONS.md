# TD-1 Logical Profile: Choices, Derivations, and Unknowns

## Purpose

After external feedback called earlier system-spec numbers into question, TD-1 needs a clean distinction between:

1. numbers that are mathematical consequences of balanced ternary;
2. numbers that are current logical architecture choices;
3. numbers that are candidate physical-design choices still waiting on hardware evidence.

A precise number is not automatically equally trustworthy just because it appears in the same spec table.

## Mathematical consequences

These statements are arithmetic facts once their premise is chosen.

### Number of states in an N-trit word

Each trit has three states, so an `N`-trit word has:

```text
3^N
```

possible patterns.

For the current `N = 12` logical profile:

```text
3^12 = 531441
```

### Signed range of a balanced-ternary N-trit word

For digits `-1, 0, +1`, the maximum magnitude is:

```text
(3^N - 1) / 2
```

For 12 trits:

```text
(3^12 - 1) / 2 = 265720
```

so the exact current 12-trit signed range is:

```text
-265720 .. +265720
```

That range is not an analog voltage claim. It follows from the logical number representation.

### Selector capacity

A `K`-trit selector can distinguish:

```text
3^K
```

states if every ternary pattern is used.

Therefore:

```text
2 trits -> 9 selector states
6 trits -> 729 selector states
```

The arithmetic is fixed. Whether TD-1 *should* dedicate 2 trits to a register selector or 6 trits to a memory address is an architecture choice.

### Five-trit balanced immediate

If a future instruction really dedicates 5 balanced trits to one signed immediate, the representable range is:

```text
-(3^5 - 1)/2 .. +(3^5 - 1)/2
= -121 .. +121
```

Again, that is a consequence of a 5-trit field, not evidence that 5 trits is the correct physical encoding choice.

## Current logical architecture choices

The Simulacrum currently chooses:

```text
word width      = 12 trits
register count  = 9
memory words    = 729
condition state = -1 / 0 / +1
```

These choices are internally coherent with the current logical ISA and software model. They are normative for the current Simulacrum profile so deterministic software artifacts can mean one thing.

They are **not** claims about:

- PCB topology;
- voltage levels;
- comparator thresholds;
- number of physical ICs;
- storage technology;
- timing;
- noise margin;
- whether a first physical prototype should implement the entire profile at once.

If real hardware evidence shows that a different word width, selector structure, or memory organization produces a materially better physical TD-1, that requires a versioned architecture decision. It should not be hidden behind adapters that pretend the physical design still matches the old profile.

## Candidate instruction allocation — not frozen

The earlier candidate layout was:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

The arithmetic bookkeeping is valid:

```text
3 + 2 + 2 + 5 = 12
3 opcode trits -> 27 raw opcode patterns
2 register trits -> 9 raw register patterns
5 immediate trits -> -121 .. +121 when interpreted as signed balanced ternary
```

What is **not** established is that this is the right physical instruction/program-image format.

Questions still requiring actual constraints include:

- whether all 27 opcode patterns should be used;
- whether two explicit register fields are worth four trits;
- whether immediate width is sufficient for real control/data-flow needs;
- whether physical memory/storage favors a different word or fetch structure;
- whether debug/programming hardware imposes alignment, framing, or error-detection needs;
- whether the eventual physical machine should expose the current logical profile directly or through a versioned translation layer.

Issue #2 remains blocked on corrected hardware inputs and first-copper evidence.

## Physical/electrical numbers — unknown until reviewed/measured

The repository deliberately does not derive these from ternary arithmetic:

- supply rails;
- logical-state voltages;
- reference voltages;
- comparator thresholds;
- hysteresis;
- resistor values;
- source/sink current;
- load/fan-out;
- propagation/settling time;
- analog tolerance/noise margins;
- environmental limits.

Balanced ternary tells us there are three logical states. It does **not** tell us the best circuit that represents them.

See [`HARDWARE_GROUND_TRUTH.md`](HARDWARE_GROUND_TRUTH.md).

## Review rule

When a TD-1 document contains a number, ask which category it belongs to:

- **Derived** — show the equation and premise.
- **Logical profile choice** — show the architecture decision/version.
- **Measured physical value** — cite the characterization evidence and unit/revision.
- **Acceptance limit** — cite the reviewed basis and measured distribution that justified the limit.
- **Unknown** — leave it unknown rather than filling the blank with a plausible-looking number.

That classification is now part of the project's engineering discipline.