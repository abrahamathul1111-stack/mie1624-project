"""Tests for the policy impact-matrix builder."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from src.scoring.policy_impact_matrix import (
    build_policy_impact_artifacts,
    load_baseline_kpis,
    strength_to_numeric_coefficient,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_KPI_PATH = PROJECT_ROOT / "outputs" / "tables" / "baseline_kpi_scores.csv"
MAPPING_PATH = PROJECT_ROOT / "data" / "processed" / "impact_matrix_long.csv"
CALIBRATION_EFFECTS_PATH = PROJECT_ROOT / "data" / "calibration" / "calibration_effects.csv"
CALIBRATION_LAGS_PATH = PROJECT_ROOT / "data" / "calibration" / "calibration_lags.csv"


class PolicyImpactMatrixTests(unittest.TestCase):
    """Regression tests for impact-matrix KPI coverage and calibration wiring."""

    def build_result(self):
        with TemporaryDirectory() as temp_dir:
            return build_policy_impact_artifacts(
                baseline_kpi_path=BASELINE_KPI_PATH,
                recommendation_mapping_path=MAPPING_PATH,
                calibration_effects_path=CALIBRATION_EFFECTS_PATH,
                calibration_lags_path=CALIBRATION_LAGS_PATH,
                output_dir=temp_dir,
            )

    def test_all_simulation_kpis_exist_in_baseline_dataset(self) -> None:
        result = self.build_result()
        baseline_kpis = set(load_baseline_kpis(BASELINE_KPI_PATH))
        simulation_kpis = set(result.metadata["KPI"])
        self.assertEqual(simulation_kpis - baseline_kpis, set())

    def test_wide_matrix_uses_full_baseline_kpi_order(self) -> None:
        result = self.build_result()
        baseline_kpis = load_baseline_kpis(BASELINE_KPI_PATH)

        self.assertEqual(list(result.matrix.columns), baseline_kpis)
        self.assertEqual(
            list(result.matrix.index),
            result.metadata.drop_duplicates("lever_name")["lever_name"].tolist(),
        )

        inactive_kpis = sorted(set(baseline_kpis) - set(result.metadata["KPI"]))
        self.assertTrue((result.matrix[inactive_kpis] == 0.0).all().all())

    def test_strength_conversion_is_monotonic_for_a_real_calibration_row(self) -> None:
        calibration_effects = pd.read_csv(CALIBRATION_EFFECTS_PATH)
        effect_row = calibration_effects.loc[
            calibration_effects["lever_id"] == "rec2_lever1"
        ].iloc[0]

        weak = strength_to_numeric_coefficient(1, effect_row)["numeric_coefficient"]
        medium = strength_to_numeric_coefficient(2, effect_row)["numeric_coefficient"]
        strong = strength_to_numeric_coefficient(3, effect_row)["numeric_coefficient"]

        self.assertGreater(medium, weak)
        self.assertGreater(strong, medium)


if __name__ == "__main__":
    unittest.main()
