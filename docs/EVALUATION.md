# Evaluation

Annotated Citrus data is the development ground truth.

## Annotated dataset schema
Current data contains fields similar to: `id_operation` (Int64), `ref_annonce` (Utf8, e.g. `RCS-A_BXA20230147`), `numero_annonce` (Int64, e.g. `853`), `ref_annonce_complet` (Utf8, e.g. `A20230147853`), `type_op` (Utf8, e.g. `VE`), `siren_cedante` and `siren_beneficiaire` (currently integers), `date_creation_op`, `date_effet_comptable_op`, and `date_realisation_juridique_op` (timestamps), and `montant` (Float64, kEUR).

Example: `ref_annonce_complet=A20230147853`, `type_op=VE`, `siren_cedante=792016313`, `siren_beneficiaire=953645579`, both effect/realization dates `11/07/2023`, and `montant=155`. Its wording states EUR 155,000, confirming 155 kEUR annotation.

## Benchmark targets
- `type_op` ↔ `typeOperation`
- `siren_cedante` ↔ `sirenCedant`
- `siren_beneficiaire` ↔ `sirenBeneficiaire`
- `date_effet_comptable_op` ↔ `dateEffetComptable`
- `date_realisation_juridique_op` ↔ `dateRealisationJuridique`
- `montant` ↔ `montantNet`

Exclude `date_creation_op`: it only records entry into Citrus. Use `ref_annonce_complet` as the primary BODACC key/benchmark join key.

## Normalization before comparison
Normalize SIRENs to 9-digit strings (zero-pad integer annotations), dates to one representation, amounts to kEUR, and missing values consistently rather than as arbitrary strings.

The offline generic API is `compare_predictions(reference_df, predictions_df)`, followed by
`summarize_metrics(comparison)`. `load_annotations_csv(path)` loads and normalizes a local
annotated CSV. Both inputs are normalized before comparison; predictions must already express
amounts in kEUR. Two null values for the same field count as equal, while a null on only one
side does not. A wholly missing prediction row is incorrect for every field. Duplicate
`ref_annonce_complet` keys raise a validation error; missing and extra keys are reported in the
summary rather than discarded.

Amount comparisons use a default tolerance of `0.1 kEUR`. This is an intentional technical
comparison tolerance, and callers may override it through `compare_predictions`.

Run the offline tests with:

```console
uv run python -m unittest discover -s tests -v
```

## Metrics
### Classification
Report overall accuracy; per-type accuracy/recall; a confusion matrix over `FU`, `AB`, `TP`, `SP`, `AP`, `ST`, `VE`, `LG`; and explicit unknown/ambiguous counts when supported.

### Field extraction
Report each target-field accuracy, metrics split by final type, and exact-row correctness across all benchmarked fields. Do not rely on global accuracy alone: classes are imbalanced, with sales historically much more common than rare scissions in sampled periods.

## Reproducibility metadata
Future outputs should identify dataset version/input path, code/commit, model, prompt/skill version where applicable, metrics, and error rows. Langfuse aids tracing, but benchmarks must be reproducible outside a trace view.
