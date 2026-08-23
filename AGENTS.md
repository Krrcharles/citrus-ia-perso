# Agent operating contract

## Repository and environment
- Active repository: `Krrcharles/citrus-ia-perso`.
- Use Python >= 3.13 and `uv` for dependency management.
- Reuse the existing architecture unless an issue explicitly requests a larger refactor.
- Prefer small, reviewable changes: one GitHub issue per PR.

## Required reading
Before modifying business logic, read `docs/PROJECT_CONTEXT.md` and `docs/DOMAIN_RULES.md`. Also read `docs/EVALUATION.md` for annotation, metric, or benchmark changes, and `docs/ROADMAP.md` for deliberate scope boundaries.

## Business invariants
- Final operation codes are exactly `FU`, `AB`, `TP`, `SP`, `AP`, `ST`, `VE`, `LG`.
- `TP` is the canonical output code. TUP is common terminology and may appear in internal names such as a `tup` skill.
- Never silently use `VE` as a generic fallback. Keep unknown or ambiguous classifications explicit until a documented rule resolves them.
- Treat SIRENs as strings of exactly 9 digits in application/evaluation logic, even when source data stores integers.
- Citrus outputs and annotations express `montantNet` / `montant` in kEUR. EUR extraction and kEUR normalization are separate steps.
- Annotated `date_creation_op` is when an operation entered Citrus, not an extraction target.

## Safety and secrets
- Never commit credentials, API keys, tokens, passwords, cookies, service-account material, or local `.env` values.
- `.gitignore` excludes `.env`; keep secrets outside the repository.
- Public BODACC examples and open-data identifiers are allowed; real credentials are not. Environment examples must use placeholders.

## Agent behavior
- Do not invent business rules. Surface missing decisions in the PR instead of guessing.
- Preserve POC behavior unless explicitly changed; do not implement roadmap phases opportunistically.
- Add/update tests for executable changes. Report commands and results in the PR summary.
- Do not invent test commands. If no automated suite exists, distinguish that fact from available validations and future desired commands.
