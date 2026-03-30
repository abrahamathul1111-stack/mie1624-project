# Included vs Excluded

## What was included
Included only canonical files required to run the final phase-based modeling pipeline notebook:
- Final submission notebook duplicate with expanded technical markdown
- Minimal source modules used by baseline, impact matrix, simulation, and attribution phases
- Local raw/processed/calibration data files required by those modules
- Canonical output tables/figures as reproducibility references and expected-output examples
- Methodology/decision references used to explain assumptions and phase framing
- Submission checks/traceability docs
- Dashboard Phase 6 component with source snapshot, data bundle, and required final HTML outputs

## What was excluded
Excluded because not required for deterministic submission notebook execution:
- report/ and presentation drafting assets not consumed by notebooks
- tests/ and __pycache__/ development artifacts
- redundant raw duplicates (for example "- Copy" variants) where a canonical equivalent exists
- exploratory or obsolete artifacts not imported by final submission notebook

## Why exclusions are safe
- Excluded files are not imported by notebooks/submission_final_pipeline.ipynb.
- Excluded files are not required by copied src module dependency paths.
- Excluded assets are delivery/reporting extras beyond the final notebook and dashboard reproducibility scope.

## Duplicate/intermediate/obsolete/test-only classes excluded
- Additional dashboard variants beyond the final required two HTML artifacts: excluded as non-essential duplicates.
- Local caches and test scripts: QA/development support only.
- Alternate duplicate raw files: canonical versions included instead.

## Repository integrity confirmation
The original repository content was preserved. No source file, notebook, data file, output file, or report asset in the original paths was modified, renamed, moved, or deleted. Work was performed by creating and populating a new folder only: submission_codepack_final/.
