# Domain rules

> Historical Citrus rules use BODACC XML; the POC uses BODACC OpenData API JSON. Paths need normalization/mapping, while the business semantics below remain the source of truth.

## RCS-A versus RCS-B
Historical integration distinguishes RCS-A registrations/*immatriculations* from RCS-B modifications and *radiations*. Equivalent data may use different paths: RCS-A main SIREN `personnes/.../numeroIdentification`; RCS-B `personnes/.../numeroIdentificationRCS`; RCS-A descriptions `acte/vente/descriptif` and `origineFonds`; RCS-B restructuring text `modificationsGenerales/descriptif`. Fusion, scission, and apport OpenData notices may instead carry their decisive free text in generic `acte.descriptif`, which remains distinct from `acte.vente.descriptif`. A future normalization layer should hide these dialects from operation skills.

## Potential SIREN
A candidate is conceptually 9 digits, possibly separated by spaces/dots. Avoid monetary/numeric false positives and validate with the existing Luhn utility. Application logic exposes normalized 9-character digit strings.

## VE — Vente
A sale requires a beneficiary and previous owner/transferor. Historical XML obtains the transferor from `PrecedentProprietairePM` / `PrecedentProprietairePP` and beneficiary from `personnes`. An actual `vente` structure or relevant sale wording must exist; `VE` is not an unknown catch-all.

Accounting-effect priority: (1) sale legal-publication/journal date; (2) `dateCommencementActivite`; (3) `dateEffet`; (4) the unique suitable description date; (5) publication date. Amount priority: (1) `origineFonds`; (2) relevant/last sale amount in the description under the historical rule. Extract EUR, then separately normalize to kEUR.

## LG — Location-gérance
For RCS-A and RCS-B, the beneficiary needs a candidate SIREN. The transferor is the previous **operator** (`PrecedentExploitantPM` / `PrecedentExploitantPP`), not the previous owner. Text must indicate `location-gérance` / `location gérance`. An operator buying its formerly leased business is `VE`, not `LG`.

The concrete LG skill uses the normalized main/current party as beneficiary and the first
previous operator with a usable SIREN as transferor. It never falls back to a previous owner
and does not duplicate an operation when several previous operators are present.

Accounting-effect priority is: (1) `dateCommencementActivite`; (2) `dateEffet`; (3) for RCS-B
only, a date after wording such as `à compter du`; (4) publication date. RCS-B legal completion
is empty at announcement-source level. For RCS-A, the historical rule table says to use the
last description date, but the historical accepted `OpA2` example uses
`dateImmatriculation` (`2018-01-11`) while accounting effect uses commencement
(`2018-01-15`). The first LG implementation therefore uses normalized
`dateImmatriculation` when available and otherwise returns empty; benchmark errors may justify
refining this decision later. Amount is always empty. Campaign-year correction based on an
older commencement year remains downstream post-processing and is not performed by the skill.

## TP / TUP
`TP` is canonical; TUP is terminology. The concrete TP skill uses RCS-B modifications only and
consumes normalized source facts. The normalized main SIREN/name are the dissolved transferor.
The beneficiary is the first ordered, Luhn-valid SIREN from `modification_description` after
excluding the main SIREN; compact, spaced and dotted forms are accepted by the common candidate
helper, while invalid and monetary candidates are rejected. A missing second candidate remains
null, and additional candidates do not create more operations. No RCS-A party fallback is used.

Documented wording covers *transmission universelle du patrimoine*, *transmission universelle de
patrimoine* and the abbreviated `transmiss.univers.patrimoine` form with practical case/accent and
separator tolerance. This predicate does not constitute a router or classifier.

Dates are read left-to-right from `modification_description`, not chronologically. Supported
forms are French textual dates (including accented/accentless February, August and December),
`DD/MM/YYYY`, `DD-MM-YYYY` and ISO `YYYY-MM-DD`; invalid calendar dates are ignored. Accounting
effect is the first valid description date, or publication date when none exists. Legal
realization is the last valid description date, or null when none exists. A single description
date populates both fields. Amount is always null, and publication year supplies the conservative
campaign year. `date_creation_op` is never an extraction input.

## Fusion / absorption / scission / apport family
The dedicated subtype router expresses every decision through the following inspectable legal
axes, in addition to its subtype, source `evidence`, and concise `reason`:

- `transfer_scope`: `TOTAL`, `PARTIAL`, or `UNKNOWN`;
- `transferor_fate`: `DISAPPEARS`, `SURVIVES`, or `UNKNOWN`;
- `beneficiary_creation`: `NEW`, `EXISTING`, or `MIXED_OR_UNKNOWN`;
- `beneficiary_count`: `ONE`, `MULTIPLE`, or `UNKNOWN`.

The subtype distinctions are:

- `FU`: total transfer and disappearance of the transferor into a beneficiary created by the operation;
- `AB`: total transfer and disappearance of the transferor into a pre-existing beneficiary;
- `SP`: partial transfer to a beneficiary created by the operation, while the transferor survives;
- `AP`: partial transfer to a pre-existing beneficiary, while the transferor survives;
- `ST`: total transfer and disappearance of the transferor, with distribution among multiple beneficiaries, whether new, existing, or mixed.

Thus FU versus AB and SP versus AP turn on whether the beneficiary is created or pre-existing;
SP and AP additionally require the transferor to survive, whereas ST requires its disappearance
and multiple beneficiaries. The deterministic consistency diagnostic checks `FU` as
`TOTAL/DISAPPEARS/NEW`, `AB` as `TOTAL/DISAPPEARS/EXISTING`, `SP` as
`PARTIAL/SURVIVES/NEW`, `AP` as `PARTIAL/SURVIVES/EXISTING`, and `ST` as
`TOTAL/DISAPPEARS` with `MULTIPLE` beneficiaries. An axis reported as unknown is preserved and
does not by itself create a contradiction. A contradiction is reported for inspection and never
silently changes the chosen subtype; `UNKNOWN` has no forced semantic profile.

These decisions use normalized free text, especially `act_description`. Future extraction may
identify main and other valid SIRENs, infer roles from phrases such as `société absorbante`,
`société bénéficiaire`, and `société scindée`, and share date/net-asset primitives. None of that
party/date/amount extraction is implemented by the subtype router. Five independent extraction
implementations are not required: a shared engine remains planned.

Historical provisional `FZ` (fusion-indeterminate) and `SZ` (scission-indeterminate) are useful internal concepts, not canonical final codes. Historical amount priority includes `Actif net apporté`, `actif net apporté égal à`, `La valeur nette des apports s'élèverait à`, `La valeur nette positive des apports s'élèverait à`, then `actif` / `actif de` proxies. Normalize EUR to kEUR.

## Semantic routing families

The first announcement-level LLM router uses an internal taxonomy distinct from final Citrus
codes: `VE`, `LG`, `TP`, `FUSION_FAMILY`, and `UNKNOWN`. The first three retain the semantics
documented above. `FUSION_FAMILY` is the temporary routing target for final annotations `FU`,
`AB`, `SP`, `ST`, and `AP`; the unchanged family router does not distinguish those five subtypes.
When it returns `FUSION_FAMILY`, the dedicated fusion subtype router can make that second decision.
`UNKNOWN` means that normalized source evidence is insufficient, ambiguous, contradictory, or
unrelated. It must not be used for malformed model output, which remains a technical failure.

Previous-owner facts may support `VE`, while previous-operator facts may support `LG`, but neither
fact alone is an invented deterministic classification rule. The router makes a semantic decision
from normalized source facts and may abstain rather than forcing a family.

## Multi-announcement / global fusion-family rules

One restructuring may yield multiple announcements, often one per legal unit. Exact descriptions
can be repeated, while participant relationships can connect branches whose descriptions differ.
Final `FU`/`AB` and `ST`/`SP` decisions therefore use a second pass after local semantic parsing.

Historical `FZ` and `SZ` remain internal provisional values:

- `FZ` is a fusion-like branch whose final `FU`/`AB` status is not yet globally resolved;
- `SZ` is a scission-like branch whose final `SP`/`ST` status is not yet globally resolved.

The faithfully reproducible historical rules are campaign-scoped and deterministic:

1. a source-established `AB` branch is an anchor; an `FZ` branch with the same non-null
   beneficiary becomes `AB`;
2. every remaining `FZ` becomes `FU`;
3. a source-established `SP` branch is an anchor; an `SZ` branch with the same non-null
   transferor becomes `SP` unless its local source facts explicitly establish `TOTAL` or
   `DISAPPEARS`;
4. a matching anchor that conflicts with local `TOTAL` or `DISAPPEARS` is recorded explicitly and
   the `SZ` branch remains `ST`; every other remaining `SZ` also becomes `ST`.

The source-established anchor signal uses normalized BODACC parties only: a previous-owner SIREN
equals the announcement's main SIREN. This equality is an `AB`/`SP` anchor signal, not a universal
participant-role definition. For fusion branches, beneficiary linkage comes from semantic
participants explicitly identified by the source description (for example, "société absorbante"
or "société bénéficiaire"); the other relevant semantic participants supply transferors.
`previous_owner` is not automatically added as a fusion transferor or beneficiary. For scission
branches, `previous_owner` may support transferor linkage, matching the historical same-transferor
propagation rule. A self-anchor branch remains observable for benchmark accounting and is not
silently removed.

Descriptions are grouped by Unicode and whitespace normalization followed by a stable exact
fingerprint. Beneficiary and transferor linkage keys use only validated source participant SIRENs
and the source publication/campaign year. There is no fuzzy clustering or annotation-based
grouping. Benchmark sampling and full runs additionally close these groups through campaign-scoped
BODACC SIREN searches; source-only linked announcements can participate in reconciliation but never
receive an inferred benchmark label.

The announcement parser exposes orthogonal facts: `legal_family` (`FUSION`, `SCISSION`, or
`UNKNOWN`), transfer scope, transferor fate, beneficiary creation, explicit partial-asset-transfer
wording (`YES`, `NO`, or `UNKNOWN`), and source-grounded participants. A partial scission may also
use the words "apport partiel d’actif"; that wording does not replace `legal_family` and does not
locally force `AP`. A direct local `AP` requires the explicit wording plus the complete supported
profile `PARTIAL`/`SURVIVES`/`EXISTING`, regardless of scission vocabulary. Conversely,
`PARTIAL`/`SURVIVES`/`NEW` establishes local `SP`, not `AP`. These orthogonal profiles are
source rules and do not depend on benchmark labels. In this operation-level model, an explicitly
partial transfer supports `SURVIVES` because the transferor retains the remainder, unless the same
source also establishes dissolution or disappearance; that contradiction remains `UNKNOWN`.

The historical notes also mention isolated `FU`/`ST` conversions to `AP`, but the available source
specification does not define the exact operation cardinality and participant-pair representation
needed to reproduce that fallback without ambiguity. This checkpoint deliberately leaves that
fallback unimplemented instead of inventing a rule. Source-explicit partial asset transfers can
still remain directly identifiable as `AP`. Final party-pair delivery, amount extraction, and date
extraction remain later work.
