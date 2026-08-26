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

## Real-data VE/LG/TP oracle benchmark

`src.modele.oracle_benchmark.run_oracle_benchmark(...)` integrates the three implemented
operation skills with real external annotations and BODACC OpenData. The equivalent CLI is:

```console
uv run python -m src.modele.oracle_benchmark \
  --annotations /path/to/operations_verifiees.parquet \
  --output-dir ./artifacts/oracle-ve-lg-smoke \
  --max-ve 50 \
  --max-lg 50 \
  --max-tp 0
```

The annotation file remains outside the repository. The runner immediately projects it onto
the lookup and generic benchmark columns, so `date_creation_op` is discarded and cannot affect
sampling, campaign year, extraction, comparison, metrics, or error reporting.

This is an extraction benchmark, not a classification benchmark. Reference `type_op` selects
only the public skill (`VE` -> `vente_skill`, `LG` -> `location_gerance_skill`,
`TP` -> `transmission_patrimoine_skill`); no other
annotation target is passed to a skill. The returned canonical type still passes through the
generic comparison, but its accuracy is structurally oracle-driven and must not be interpreted
as classifier quality.

Rows are sorted by `ref_annonce_complet` within each type before applying the limits. CLI
defaults are 50 VE, 50 LG and 0 TP for backwards compatibility. A zero limit disables a type,
and `all` requests its full filtered sample. Other annotated types are counted as out of scope
rather than failures.

TP smoke runs are deterministic and require no LLM credentials:

```console
uv run python -m src.modele.oracle_benchmark \
  --annotations /path/to/operations_verifiees.parquet \
  --output-dir ./artifacts/oracle-tp-smoke \
  --max-ve 0 \
  --max-lg 0 \
  --max-tp 50
```

Current annotation references are resolved without transformation. For the documented example,
`ref_annonce=RCS-A_BXA20230147` and `numero_annonce=853` must agree exactly with the directly
usable OpenData `id` `ref_annonce_complet=A20230147853`. Unsupported or inconsistent triples
produce a per-row lookup-resolution error; the runner never fabricates an identifier.

Before extraction, selected rows with a null/blank `ref_annonce_complet`, plus every occurrence
of a duplicated key in the selected sample, are recorded as `lookup_resolution` failures and
excluded from the benchmark reference. They are not assigned surrogate keys or deduplicated.
Coverage reports both selected and benchmark-eligible counts, including explicit
`invalid_join_key` and `duplicate_join_key` failures. Rows with a valid unique key remain in the
generic benchmark even when later lookup, fetch, or skill execution fails, so they continue to
appear as missing predictions.

The output directory contains:

- `predictions.parquet`: successful canonical predictions plus `oracle_type`;
- `comparison.parquet`: normalized rows and correctness flags returned by the generic benchmark;
- `errors.parquet`: pipeline failures and incorrect benchmark rows with expected/predicted values;
- `summary.json`: reproducibility metadata, VE/LG/TP coverage, failure-stage counts, and the unchanged
  `summarize_metrics` result.

Inspect `summary.json`, then group/filter `comparison.parquet` and `errors.parquet` by `type_op`,
`failure_stage`, and `failing_fields`. VE uses the existing configured LLM environment; LG and TP
are deterministic source/debug paths. Generated `artifacts/` remain local and are ignored by Git.

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
