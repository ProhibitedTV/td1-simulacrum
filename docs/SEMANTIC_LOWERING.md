# Typed State Weave Lowering

## Purpose

TD-1's native operator language should not become a decorative alias for assembly. A State Weave names an abstract semantic operation; execution additionally requires concrete machine resources such as registers and memory addresses.

The v1 lowering layer makes that boundary explicit.

```text
State Weave identity
      |
      v
explicit OperandBindings
      |
      v
td1.semantic-lowering / v1
      |
      v
logical TD-1 instructions
      |
      v
reference machine / execution trace
```

> Semantic identity is not an excuse to hide operands.

## Epistemic boundary

The supported v1 mappings are **TD-1 engineering conventions**. They are not translations discovered in the Veilbreak corpus, and they do not establish that reported phenomenology encodes a computer language.

Veilbreak-derived motifs can influence interface structure and representation through the existing frozen-corpus provenance pipeline. Arithmetic meaning and executable lowering remain independently specified engineering decisions.

## Schema

```text
td1.semantic-lowering / v1
```

A lowering artifact preserves:

- canonical source State Weave;
- project-defined semantic action;
- explicit operand bindings;
- exact logical instruction sequence;
- register reads and writes;
- memory effect (`none`, `read`, or `write`);
- deterministic canonical JSON and SHA-256 digest.

Deserialization recompiles the source weave and bindings and requires the result to match the serialized artifact. A saved lowering therefore cannot quietly substitute a different logical instruction sequence.

## Supported v1 forms

The initial executable surface is deliberately small:

| State Weave | Action | Required operands | Logical ISA |
| --- | --- | --- | --- |
| `EXECUTION:-` | halt | none | `HALT` |
| `TRANSFORM:-` | negate | `target_register` | `NEG target` |
| `STATE:0` | compare | `left_register`, `right_register` | `CMP left,right` |
| `MEMORY:0` | memory read | `target_register`, `base_register` | `LD target,base,offset` |
| `MEMORY:+` | memory write | `source_register`, `base_register` | `ST source,base,offset` |

`offset` is optional for the memory forms and defaults to logical zero when absent.

Unsupported State Weaves fail with `UnsupportedWeaveError`. A supported form with missing, extraneous, or invalid machine operands fails separately with `OperandBindingError`.

That distinction is intentional: callers can tell the difference between **"TD-1 does not know how to execute this semantic form"** and **"the form is executable, but you bound it incorrectly."**

## Why only five forms

TD-1 currently has semantic roots such as `TIME`, `OBSERVER`, `REFERENCE`, `COGNITION`, `FRAME`, and `DOMAIN` whose useful behavior lives partly or entirely outside the present 15-op logical ISA.

Inventing a fake one-instruction translation for those roots would create the appearance of completeness while silently destroying meaning.

The compiler therefore prefers an explicit unsupported state over a misleading implementation.

Future lowering revisions may add:

- compound multi-root forms;
- Observer Continuity operations;
- branch/control structures;
- address/value construction;
- semantic temporary allocation;
- multi-instruction lowering plans;
- explicit capability requirements;
- hardware-backed semantic operations.

Each addition must remain testable against the reference machine and must not depend on renderer behavior.

## Operand bindings

`OperandBindings` names concrete resources instead of using ambiguous positional arguments:

```python
OperandBindings(
    target_register=2,
    base_register=0,
    offset=8,
)
```

TD-1 has nine general-purpose registers, so register bindings must be in `R0..R8`.

A lowering form accepts only its declared operands. For example, `STATE:0` rejects an `offset` because comparison does not use one.

## CLI

List the complete supported v1 surface:

```bash
td1-sim lowerings
```

Lower a halt weave:

```bash
td1-sim lower 'EXECUTION:-'
```

Lower a negation:

```bash
td1-sim lower 'TRANSFORM:-' --target R2
```

Lower a memory read:

```bash
td1-sim lower 'MEMORY:0' --target R2 --base R0 --offset 8
```

For smoke testing, `--execute` runs the lowered fragment on a zeroed reference machine. If the lowering itself does not halt, the CLI appends an engineering-only `HALT` after the fragment so the demonstration run terminates. That appended halt is not part of the lowering artifact.

## Relationship to physical instruction encoding

This layer lowers into the existing **logical** `Instruction(op,a,b,imm)` representation only.

It deliberately does not assign any physical 12-trit opcode pattern.

Issue #2 can now review a real semantic compiler boundary before deciding whether the proposed physical layout

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

is still the right hardware contract.

The rule remains:

> Native semantics first. Logical correctness second. Copper encoding last.
