# Technical Method Summary

This submission package implements a deterministic, phase-based pipeline:

1. Baseline reconstruction from workbook + Canada gap reference.
2. Calibration-aware recommendation-to-KPI impact matrix synthesis.
3. Quarterly state-transition simulation with Monte Carlo draws.
4. Median trajectory extraction and scenario comparison outputs.
5. KPI gap reduction attribution against peer-best and global-best benchmarks.

Modeling is intentionally local-file based for reproducibility. The submission notebook uses phase headers, explicit inputs/outputs, and local path conventions suitable for auditability by data scientists and ML engineers.
