# Project context

## Purpose
Citrus IA extracts structured company-restructuring information from French BODACC legal announcements. For announcements already treated as sales (`VE`), the existing POC demonstrates the extraction and evaluation path: (1) fetch an announcement, (2) clean/normalize its payload, (3) apply the `VE` extraction logic with deterministic rules and LLM calls where useful, and (4) compare predictions with annotated Citrus data. A first semantic router classifies normalized announcements by family. The original dedicated `fusion-subtype-v1` router remains available as an announcement-only diagnostic baseline, but final `FUSION_FAMILY` classification now follows a two-pass boundary because one announcement may not contain the cross-company evidence needed for `FU`/`AB` or `SP`/`ST`. This checkpoint classifies the family without extracting final parties, dates, or amounts. The goal is all eight types, developed incrementally and measurably.

## Target restructuring taxonomy
- `FU` — **Fusion**: several companies disappear to form a newly created beneficiary.
- `AB` — **Absorption**: transferor companies disappear into an existing beneficiary.
- `TP` — **Transmission universelle de patrimoine (TUP)**: dissolution without liquidation, transferring all assets to the sole corporate shareholder.
- `SP` — **Scission partielle**: the transferor survives and transfers part of its assets to company/companies created for the operation.
- `AP` — **Apport partiel d'actifs**: the transferor survives and transfers part of its assets to an existing beneficiary.
- `ST` — **Scission totale**: the transferor disappears and its assets are split among several existing or new beneficiaries.
- `VE` — **Vente**: partial asset transfer for purely financial consideration; Citrus mostly targets *fonds de commerce* sales.
- `LG` — **Location-gérance**: an owner grants operation rights without ownership transfer; historically an operation may occur at both lease start and end.

The POC README formerly listed four categories. This eight-type taxonomy supersedes that old **target** description, without implying all parsers exist today.

## Design decisions already made
1. Preserve the POC shape: one BODACC announcement produces a Citrus-like output.
2. Do not require a complex event model yet. Later global post-processing may reconcile announcements, but the primary extraction unit remains one announcement.
3. Annotated data—not the current Citrus extraction implementation—is the development benchmark/ground truth.
4. Classification first routes to a semantic family, then uses a family-specific router where a finer final decision is required. Extraction remains a separate boundary.
5. Refine uncertainty policy later; for now, avoid forced unsupported classifications.
6. Add MCP after the Python engine is reliable. MCP is an adapter and must not duplicate business rules.

## Operation skill boundary

An operation skill exposes an `operation_type` code and one `extract(announcement)` method
that returns the announcement-level Citrus business fields. `VenteSkill` is the first
implementation, `LocationGeranceSkill` is the second and `TransmissionPatrimoineSkill` is the
third. The public singletons `src.operation.vente_skill`,
`src.operation.location_gerance_skill` and `src.operation.transmission_patrimoine_skill`
provide the canonical VE, LG and TP entry points. TUP remains common terminology, while TP is
the final code. VE deliberately delegates to its existing helpers, while LG and TP consume only
`NormalizedBodaccAnnouncement` source facts. Classification, routing, dataset keys, and benchmark
joins remain outside this small boundary.

## BODACC normalization boundary

`src.bodacc.normalize_bodacc_announcement(raw_payload)` returns a frozen
`NormalizedBodaccAnnouncement` without changing the caller's mapping. Nested
OpenData containers are parsed from JSON strings or copied from existing dict/list
values, while a deep copy of the original payload remains available as
`raw_payload` for diagnostics.

The object exposes a conservative `RCS-A` / `RCS-B` / `UNKNOWN` dialect;
ordered current persons, previous owners and previous operators; first-current-person
`main_siren` and `main_name` conveniences; generic `acte.descriptif`, RCS-A
`acte.vente.descriptif`, and RCS-B `modificationsGenerales.descriptif` text as
separate source facts;
RCS-A immatriculation category and date; publication, commencement, effect and sale
legal-publication source dates; source URL; and every establishment `origineFonds`.
These are source facts only: no
operation classification, party-role inference, accounting-date priority or amount
normalization occurs here.

`src.bodacc.extract_siren_candidates(text, excluded_sirens=...)` finds compact,
space-separated or dot-separated 9-digit candidates, preserves first occurrence,
deduplicates, applies Luhn validation, supports exclusions and rejects candidates
immediately presented as EUR/euro amounts. It does not infer a role for a candidate.

## Semantic family-routing boundary

`src.routing.family_router.route(raw_announcement)` accepts one raw BODACC mapping and always
normalizes it before constructing the LLM prompt. The deterministic routing context contains only
the detected dialect, main party, distinct act/sale/modification descriptions, distinct
origin-of-funds values, immatriculation category, previous owners and previous operators. It excludes the raw
payload, annotation labels and targets, `type_op`, and `date_creation_op`.

The router returns exactly one internal family among `VE`, `LG`, `TP`, `FUSION_FAMILY` and
`UNKNOWN`. `FUSION_FAMILY` temporarily groups `FU`, `AB`, `SP`, `ST` and `AP`; `UNKNOWN` is a
valid semantic abstention. Malformed LLM JSON or schema violations are technical errors rather
than abstentions. The versioned `family-router-v1` prompt uses the existing Langfuse-instrumented
LLM client at temperature zero. Routing does not call operation skills, and skill dispatch remains
outside this boundary. `family-router-v1` remains unchanged: the intended classification chain is
`family router -> FUSION_FAMILY -> fusion subtype router -> FU/AB/SP/ST/AP/UNKNOWN`.

## Fusion subtype-routing boundary

`src.routing.fusion_subtype.FusionSubtypeRouter.route(raw_announcement)` is specialized solely
for announcements already considered part of `FUSION_FAMILY`. It normalizes the raw mapping itself
with `normalize_bodacc_announcement` and builds a compact context from normalized source facts,
including `act_description`. It never invokes the family router or an operation skill. Neither
`type_op`, annotations, nor extraction targets are accepted as LLM context.

Each valid `FusionSubtypeResult` contains one subtype among `FU`, `AB`, `SP`, `ST`, `AP`, and
`UNKNOWN`, plus four inspectable legal axes: `transfer_scope` (`TOTAL`, `PARTIAL`, `UNKNOWN`),
`transferor_fate` (`DISAPPEARS`, `SURVIVES`, `UNKNOWN`), `beneficiary_creation` (`NEW`, `EXISTING`,
`MIXED_OR_UNKNOWN`), `beneficiary_count` (`ONE`, `MULTIPLE`, `UNKNOWN`), `evidence`, and `reason`.
The versioned `fusion-subtype-v1` prompt and `fusion-subtype-routing-v1` taxonomy make the FU/AB,
SP/AP, and ST distinctions explicit and use `src.llm.client` at temperature zero.

Deterministic helpers report semantic inconsistencies between a chosen subtype and its axes. They
are diagnostics only: they neither replace nor silently correct the LLM subtype. Invalid JSON or
schema values remain technical errors, while `UNKNOWN` remains a valid semantic abstention. This
router performs classification only; fusion-family transferor/beneficiary, date, and amount
extraction remains a later phase.

`fusion-subtype-v1` is intentionally preserved unchanged. Its row-independent final-label output is
useful for local diagnostics and comparison, but is not the authoritative final complex-family
decision when several announcements describe one restructuring.

## Fusion semantic parsing and global reconciliation boundary

The authoritative complex-family classification path is:

```text
normalized announcement
-> announcement-level `fusion-semantics-v1` facts and participants
-> internal provisional branch (`FZ`, `SZ`, or a source-established anchor)
-> deterministic campaign/global reconciliation
-> final `FU`, `AB`, `SP`, `ST`, `AP`, or `UNKNOWN`
```

The local parser reports only source-supported `legal_family`, transfer scope, transferor fate,
beneficiary creation status, explicit partial-asset-transfer wording, participants with semantic
roles, short evidence, and a reason. These axes are orthogonal: explicit
`PARTIAL`/`SURVIVES`/`EXISTING` with partial-asset-transfer wording establishes AP even
alongside scission vocabulary, while `PARTIAL`/`SURVIVES`/`NEW` establishes SP. It does not emit
a final Citrus subtype. Every non-null participant SIREN must be present in the normalized context
and pass the common deterministic validation. Missing legal facts remain explicitly unknown.

The provisional and reconciliation layers are pure source-data transformations. Exact normalized
description fingerprints and source-derived participant linkage keys connect related branches;
annotation labels and benchmark correctness fields are excluded. `FZ` and `SZ` are internal only
and never expand the canonical Citrus output taxonomy. The reconciler does not call an LLM,
network service, operation skill, or final extraction engine.

## Common output contract
The intended logical output contains `ref_annonce_complet`, `anneeCampagne`, `typeOperation`, `sirenCedant`, `sirenBeneficiaire`, `dateEffetComptable`, `dateRealisationJuridique`, `montantNet`, and `source`.

The POC also extracts `raisonSocialeCedant` and `raisonSocialeBeneficiaire`; they may remain useful but are not current annotated benchmark targets. `source` identifies `BODACC` or its announcement URL as appropriate to the existing implementation; representation may later be normalized without changing business semantics.

## VE/LG/TP integration benchmark boundary

The real-data oracle runner uses external local annotations and their `type_op` only to choose
between the already-public VE, LG and TP skills. It resolves and fetches one real BODACC announcement,
keeps row-level pipeline failures observable, and delegates every comparison and metric to the
generic benchmark. It does not classify operations, add a router, or change any skill's business
rules. `date_creation_op` remains outside extraction and evaluation entirely.
