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

## Real-data semantic family-routing benchmark

`src.modele.routing_benchmark.run_routing_benchmark(...)` evaluates the LLM family router alone.
It is separate from `oracle_benchmark`: it never calls VE/LG/TP extraction skills and does not
evaluate extracted parties, dates, or amounts. A future router-to-skill end-to-end benchmark is a
third, deliberately unimplemented layer.

The loader immediately projects external annotations onto `ref_annonce`, `numero_annonce`,
`ref_annonce_complet`, and `type_op`; `date_creation_op` and all extraction targets are absent from
routing inputs. `type_op` is used only after routing to map reference families: `VE -> VE`,
`LG -> LG`, `TP -> TP`, and `FU/AB/SP/ST/AP -> FUSION_FAMILY`. Null, blank, and non-canonical
reference types are reported as unsupported and never passed to the router. Tests inject sentinel
reference values through both annotation and fetched-payload paths to verify they cannot enter the
normalized routing context or LLM messages.

Sampling is deterministic within each of the eight final annotated types: rows are sorted by
`ref_annonce_complet`, then `--max-per-type` is applied before reference-family mapping. The default
is 10, limiting a balanced run to roughly 80 LLM calls; `all` explicitly requests the full sample.
Invalid/blank and duplicated join keys are observable and excluded, while eligible rows remain in
the metric denominator after lookup-resolution, fetch, LLM-execution, or output-validation failure.

Routing metrics include overall accuracy, recall/precision/F1 per known reference family, macro
recall, macro F1, semantic UNKNOWN count/rate, non-UNKNOWN coverage, selective accuracy, and a
confusion matrix. Matrix rows are `VE`, `LG`, `TP`, and `FUSION_FAMILY`; columns additionally
separate `UNKNOWN` from technical `__ERROR__`. `FUSION_FAMILY` results retain an inspection
breakdown by final `FU`, `AB`, `SP`, `ST`, and `AP` type. Macro metrics average the known reference
families that have support in the selected sample; the summary records that family count.

The output directory contains:

- `routing_predictions.parquet`: one valid router output per row with key, original final type,
  reference/predicted family, correctness, reason, and list-valued evidence;
- `routing_errors.parquet`: technical pipeline failures plus semantic UNKNOWN/misclassification
  rows with stages, codes, expected/predicted families, reason, and evidence where applicable;
- `routing_summary.json`: timestamp, commit, annotation filename, sample limit, selected and
  eligible counts by final type/family, configured model name, prompt/taxonomy versions, failure
  counts, coverage, routing metrics, confusion matrix, and artifact names.

Run the first balanced real-data smoke only when credentials and the external annotations are
available:

```console
uv run --env-file .env -- python -m src.modele.routing_benchmark \
  --annotations /path/to/operations_verifiees.parquet \
  --output-dir ./artifacts/router-smoke \
  --max-per-type 10
```

Inspect this honest baseline before changing the prompt or adding routing shortcuts. Automated
tests inject fake LLM responses and never call the real endpoint.

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
