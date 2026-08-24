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

## Phase 4 — Family router
Route first to `VE`, `LG`, `TP`, fusion/scission/apport, or unknown/ambiguous rather than forcing all eight final types.

## Phase 5 — LG
Implement and benchmark location-gérance.

## Phase 6 — TP / TUP
Implement and benchmark transmission universelle de patrimoine. Internal naming may use `tup`; output must use `TP`.

## Phase 7 — Shared fusion/scission/apport engine
Build shared SIREN, role, date, and amount primitives before splitting final types.

## Phase 8 — Final complex types
Support final `FU`, `AB`, `SP`, `ST`, `AP` decisions and benchmark annotations.

## Phase 9 — Global post-processing
Add multi-announcement reconciliation/deduplication and historical global reclassification only after announcement-level extraction is measurable.

## Phase 10 — Quality / observability
Stabilize regression metrics, experiment metadata, prompt/skill versioning, and Langfuse.

## Phase 11 — MCP exposure
Expose the stable Python engine through MCP tools/skills. MCP is an adapter; business rules stay in the Python domain layer.

**Project rule: do not start the next operation type until the current one is integrated into the generic benchmark and its errors can be inspected.**
