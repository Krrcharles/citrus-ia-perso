# Project context

## Purpose
Citrus IA extracts structured company-restructuring information from French BODACC legal announcements. For announcements already treated as sales (`VE`), the existing POC demonstrates the extraction and evaluation path: (1) fetch an announcement, (2) clean/normalize its payload, (3) apply the `VE` extraction logic with deterministic rules and LLM calls where useful, and (4) compare predictions with annotated Citrus data. General classification and routing across operation types are still work in progress and are not part of the currently demonstrated path. The goal is all eight types, developed incrementally and measurably.

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
4. Classification may first route to a family/skill and then make the final family-specific decision.
5. Refine uncertainty policy later; for now, avoid forced unsupported classifications.
6. Add MCP after the Python engine is reliable. MCP is an adapter and must not duplicate business rules.

## Common output contract
The intended logical output contains `ref_annonce_complet`, `anneeCampagne`, `typeOperation`, `sirenCedant`, `sirenBeneficiaire`, `dateEffetComptable`, `dateRealisationJuridique`, `montantNet`, and `source`.

The POC also extracts `raisonSocialeCedant` and `raisonSocialeBeneficiaire`; they may remain useful but are not current annotated benchmark targets. `source` identifies `BODACC` or its announcement URL as appropriate to the existing implementation; representation may later be normalized without changing business semantics.
