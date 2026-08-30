# Roadmap

Later phases are deliberately out of scope until earlier phases are measurable.

## Phase 0 — Project memory / documentation
This issue: version the project context, rules, evaluation contract, roadmap, and agent instructions.

## Phase 1 — Generic benchmark
Generalize sale-only evaluation to load, normalize, and measure the annotated multi-type dataset with common metrics.

## Phase 2 — Refactor VE into the first operation skill (implemented)
Existing `VE` behavior is available behind the minimal operation-skill boundary and covered by offline regression tests.

## Phase 3 — BODACC normalization layer (implemented)
RCS-A/RCS-B/raw JSON differences are hidden behind non-mutating accessors for main SIREN, descriptions, previous owners/operators, source dates, origin of funds, and candidate SIRENs.

## Phase 4 — LG (implemented before the router)
Location-gérance is extracted and benchmarked as the second concrete operation skill. This
intentional sequencing validates the normalization/skill boundary with both RCS-A and RCS-B.

### VE/LG/TP real-data validation checkpoint
The oracle-type runner exercises VE/LG/TP extraction against external annotations and real
BODACC announcements, with generic metrics and inspectable row failures. TP can run alone as a
deterministic smoke path without LLM credentials.

## Phase 5 — Family router (implemented after TP)
The normalized semantic LLM router now targets `VE`, `LG`, `TP`, `FUSION_FAMILY`, or `UNKNOWN`
without forcing all eight final types. Its dedicated real-data benchmark measures classification
separately from extraction, with deterministic per-final-type sampling, leakage safeguards,
abstention-aware metrics and inspectable errors. TP was deliberately pulled forward to validate
the normalized extraction boundary; no router is part of the TP skill itself. The versioned
`family-router-v1` remains unchanged.

## Phase 6 — TP / TUP (implemented before the router)
Transmission universelle de patrimoine is implemented and oracle-benchmarkable as the third
normalized-native skill. TUP remains common terminology; the output code is always `TP`.

## Phase 7 — Fusion subtype router (diagnostic baseline implemented)
The dedicated second-stage LLM router refines `FUSION_FAMILY` into `FU`, `AB`, `SP`, `ST`, `AP`,
or semantic `UNKNOWN`. It also exposes transfer scope, transferor fate, beneficiary creation/count,
evidence, reason, and a deterministic non-corrective consistency diagnostic. Its isolated benchmark
bypasses the family router and all extraction skills, samples five rows per type by default (or
`all`), and reports abstention-, technical-error-, confusion-, and semantic consistency metrics.

## Phase 8 — Fusion semantic parser and global reconciliation (current checkpoint)

Parse source-supported legal facts and minimally required participants announcement by announcement,
using orthogonal legal-family, transfer-scope, transferor-fate, beneficiary-creation, and explicit
partial-asset-transfer-wording axes. Wording such as "apport partiel d'actif" may coexist with a
partial scission and never forces AP by itself. Construct internal `FZ`/`SZ` branches, then reconcile
related campaign rows deterministically by beneficiary for fusions and transferor for scissions into
final `FU`, `AB`, `SP`, `ST`, `AP`, or `UNKNOWN`. The benchmark preserves linked groups and keeps
the full run authoritative. The original Phase 7 router remains unchanged for comparison.

## Phase 9 — Shared fusion/scission/apport extraction engine (later)

Build shared final SIREN-pair, date, and amount primitives, then extract transferor, beneficiary,
dates, and amounts for final `FU`, `AB`, `SP`, `ST`, and `AP` delivery rows. Minimal participants
used by Phase 8 for linkage are not a final extraction engine.

## Phase 10 — Quality / observability
Stabilize regression metrics, experiment metadata, prompt/skill versioning, and Langfuse.

## Phase 11 — MCP exposure
Expose the stable Python engine through MCP tools/skills. MCP is an adapter; business rules stay in the Python domain layer.

**Project rule: do not start the next operation type until the current one is integrated into the generic benchmark and its errors can be inspected.**
