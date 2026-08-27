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
`FU`, `AB`, `SP`, `ST`, and `AP` share logic: use free text; identify main and other valid SIRENs; infer roles from phrases such as `société absorbante`, `société bénéficiaire`, and `société scindée`; share date/net-asset primitives. Five independent initial implementations are not required: a shared engine is planned.

Historical provisional `FZ` (fusion-indeterminate) and `SZ` (scission-indeterminate) are useful internal concepts, not canonical final codes. Historical amount priority includes `Actif net apporté`, `actif net apporté égal à`, `La valeur nette des apports s'élèverait à`, `La valeur nette positive des apports s'élèverait à`, then `actif` / `actif de` proxies. Normalize EUR to kEUR.

## Semantic routing families

The first announcement-level LLM router uses an internal taxonomy distinct from final Citrus
codes: `VE`, `LG`, `TP`, `FUSION_FAMILY`, and `UNKNOWN`. The first three retain the semantics
documented above. `FUSION_FAMILY` is the temporary routing target for final annotations `FU`,
`AB`, `SP`, `ST`, and `AP`; the router does not distinguish those five subtypes yet. `UNKNOWN`
means that normalized source evidence is insufficient, ambiguous, contradictory, or unrelated.
It must not be used for malformed model output, which remains a technical failure.

Previous-owner facts may support `VE`, while previous-operator facts may support `LG`, but neither
fact alone is an invented deterministic classification rule. The router makes a semantic decision
from normalized source facts and may abstain rather than forcing a family.

## Multi-announcement / global rules — later phase
One restructuring may yield multiple announcements (often one per legal unit); identical descriptions can duplicate operations; cross-announcement evidence can distinguish `FU`/`AB` and `ST`/`SP`. Historical Citrus globally reclassified provisional operations and could remove technical pairs where `sirenCedant == sirenBeneficiaire` after they served as evidence. Do not implement this now: keep announcement-level POC compatibility and add reconciliation later as a second pass.
