# Domain rules

> Historical Citrus rules use BODACC XML; the POC uses BODACC OpenData API JSON. Paths need normalization/mapping, while the business semantics below remain the source of truth.

## RCS-A versus RCS-B
Historical integration distinguishes RCS-A registrations/*immatriculations* from RCS-B modifications and *radiations*. Equivalent data may use different paths: RCS-A main SIREN `personnes/.../numeroIdentification`; RCS-B `personnes/.../numeroIdentificationRCS`; RCS-A descriptions `acte/vente/descriptif` and `origineFonds`; RCS-B restructuring text `modificationsGenerales/descriptif`. A future normalization layer should hide these dialects from operation skills.

## Potential SIREN
A candidate is conceptually 9 digits, possibly separated by spaces/dots. Avoid monetary/numeric false positives and validate with the existing Luhn utility. Application logic exposes normalized 9-character digit strings.

## VE — Vente
A sale requires a beneficiary and previous owner/transferor. Historical XML obtains the transferor from `PrecedentProprietairePM` / `PrecedentProprietairePP` and beneficiary from `personnes`. An actual `vente` structure or relevant sale wording must exist; `VE` is not an unknown catch-all.

Accounting-effect priority: (1) sale legal-publication/journal date; (2) `dateCommencementActivite`; (3) `dateEffet`; (4) the unique suitable description date; (5) publication date. Amount priority: (1) `origineFonds`; (2) relevant/last sale amount in the description under the historical rule. Extract EUR, then separately normalize to kEUR.

## LG — Location-gérance
For RCS-A and RCS-B, the beneficiary needs a candidate SIREN. The transferor is the previous **operator** (`PrecedentExploitantPM` / `PrecedentExploitantPP`), not the previous owner. Text must indicate `location-gérance` / `location gérance`. An operator buying its formerly leased business is `VE`, not `LG`.

Accounting-effect priority: (1) `dateCommencementActivite`; (2) `dateEffet`; (3) RCS-B date after wording such as `à compter du`; (4) publication date. Legal completion is the last relevant description date for historical RCS-A and empty for historical RCS-B. Amount is empty.

## TP / TUP
`TP` is canonical; TUP is terminology. Historically this primarily uses RCS-B modifications: the main SIREN is the dissolved transferor, a different valid description SIREN is beneficiary, and wording must indicate *transmission universelle de patrimoine*. Amount is empty. Accounting effect is the first relevant description date or publication fallback; legal realization is the last relevant date.

## Fusion / absorption / scission / apport family
`FU`, `AB`, `SP`, `ST`, and `AP` share logic: use free text; identify main and other valid SIRENs; infer roles from phrases such as `société absorbante`, `société bénéficiaire`, and `société scindée`; share date/net-asset primitives. Five independent initial implementations are not required: a shared engine is planned.

Historical provisional `FZ` (fusion-indeterminate) and `SZ` (scission-indeterminate) are useful internal concepts, not canonical final codes. Historical amount priority includes `Actif net apporté`, `actif net apporté égal à`, `La valeur nette des apports s'élèverait à`, `La valeur nette positive des apports s'élèverait à`, then `actif` / `actif de` proxies. Normalize EUR to kEUR.

## Multi-announcement / global rules — later phase
One restructuring may yield multiple announcements (often one per legal unit); identical descriptions can duplicate operations; cross-announcement evidence can distinguish `FU`/`AB` and `ST`/`SP`. Historical Citrus globally reclassified provisional operations and could remove technical pairs where `sirenCedant == sirenBeneficiaire` after they served as evidence. Do not implement this now: keep announcement-level POC compatibility and add reconciliation later as a second pass.
