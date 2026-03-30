"""Regression tests for the quarterly state-transition simulator."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from src.simulation import (
    SCENARIO_DEFINITIONS,
    StateTransitionConfig,
    load_simulation_inputs,
    run_quarterly_state_transition,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_COUNTRY_PATH = PROJECT_ROOT / "outputs" / "tables" / "baseline_country_scores.csv"
BASELINE_KPI_PATH = PROJECT_ROOT / "outputs" / "tables" / "baseline_kpi_scores.csv"
IMPACT_MATRIX_PATH = PROJECT_ROOT / "outputs" / "tables" / "impact_matrix.csv"
IMPACT_METADATA_PATH = PROJECT_ROOT / "outputs" / "tables" / "impact_matrix_long.csv"
CALIBRATION_EFFECTS_PATH = PROJECT_ROOT / "data" / "calibration" / "calibration_effects.csv"
CALIBRATION_LAGS_PATH = PROJECT_ROOT / "data" / "calibration" / "calibration_lags.csv"
COMPETITOR_DRIFT_PATH = PROJECT_ROOT / "data" / "calibration" / "competitor_drift.csv"
IMPLEMENTATION_SCHEDULE_PATH = (
    PROJECT_ROOT / "data" / "calibration" / "implementation_schedule.csv"
)


class StateTransitionSimulationTests(unittest.TestCase):
    """Regression tests for scenario coverage, alignment, and baseline behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        cls.config = StateTransitionConfig(quarters=8, draws=64, random_seed=17)
        cls.inputs = load_simulation_inputs(
            config=cls.config,
            baseline_country_path=BASELINE_COUNTRY_PATH,
            baseline_kpi_path=BASELINE_KPI_PATH,
            impact_matrix_path=IMPACT_MATRIX_PATH,
            impact_metadata_path=IMPACT_METADATA_PATH,
            implementation_schedule_path=IMPLEMENTATION_SCHEDULE_PATH,
            calibration_effects_path=CALIBRATION_EFFECTS_PATH,
            calibration_lags_path=CALIBRATION_LAGS_PATH,
            competitor_drift_path=COMPETITOR_DRIFT_PATH,
        )
        cls.result = run_quarterly_state_transition(
            config=cls.config,
            baseline_country_path=BASELINE_COUNTRY_PATH,
            baseline_kpi_path=BASELINE_KPI_PATH,
            impact_matrix_path=IMPACT_MATRIX_PATH,
            impact_metadata_path=IMPACT_METADATA_PATH,
            implementation_schedule_path=IMPLEMENTATION_SCHEDULE_PATH,
            calibration_effects_path=CALIBRATION_EFFECTS_PATH,
            calibration_lags_path=CALIBRATION_LAGS_PATH,
            competitor_drift_path=COMPETITOR_DRIFT_PATH,
            output_dir=cls.temp_dir.name,
        )
        cls.baseline_country_scores = pd.read_csv(BASELINE_COUNTRY_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_policy_and_drift_kpis_align_with_the_baseline_catalog(self) -> None:
        baseline_kpis = set(self.inputs.kpis)
        self.assertTrue(set(self.inputs.impact_metadata["KPI"]).issubset(baseline_kpis))
        self.assertTrue(set(self.inputs.drift_priors["kpi"]).issubset(baseline_kpis))
        self.assertTrue(
            set(self.inputs.impact_metadata["calibration_lag_lever_id"]).issubset(
                set(self.inputs.schedule_profiles)
            )
        )

    def test_baseline_scenario_starts_from_the_exported_canada_baseline(self) -> None:
        canada_expected = self.baseline_country_scores.loc[
            self.baseline_country_scores["country"] == "Canada"
        ].iloc[0]
        canada_q1 = self.result.country_quarter_scores.loc[
            (self.result.country_quarter_scores["scenario"] == "baseline")
            & (self.result.country_quarter_scores["quarter_index"] == 1)
            & (self.result.country_quarter_scores["country"] == "Canada")
        ].iloc[0]

        self.assertAlmostEqual(
            float(canada_q1["composite_score"]),
            float(canada_expected["composite_score"]),
            places=6,
        )
        self.assertAlmostEqual(
            float(canada_q1["rank"]),
            float(canada_expected["rank"]),
            places=6,
        )

    def test_expected_scenarios_and_requested_quarters_are_exported(self) -> None:
        exported_scenarios = set(self.result.country_quarter_scores["scenario"])
        self.assertEqual(exported_scenarios, set(SCENARIO_DEFINITIONS))

        quarter_counts = (
            self.result.country_quarter_scores.groupby("scenario")["quarter_index"]
            .nunique()
            .to_dict()
        )
        for scenario_name in SCENARIO_DEFINITIONS:
            self.assertEqual(quarter_counts[scenario_name], self.config.quarters)

        for export_path in self.result.export_paths.values():
            self.assertTrue(Path(export_path).exists())

    def test_all_recommendations_improve_canada_composite_by_final_quarter(self) -> None:
        final_quarter = self.config.quarters
        baseline_final = self.result.canada_rank_trajectory.loc[
            (self.result.canada_rank_trajectory["scenario"] == "baseline")
            & (self.result.canada_rank_trajectory["quarter_index"] == final_quarter),
            "composite_score_median",
        ].iloc[0]
        all_recommendations_final = self.result.canada_rank_trajectory.loc[
            (self.result.canada_rank_trajectory["scenario"] == "all_recommendations")
            & (self.result.canada_rank_trajectory["quarter_index"] == final_quarter),
            "composite_score_median",
        ].iloc[0]

        self.assertGreater(float(all_recommendations_final), float(baseline_final))


if __name__ == "__main__":
    unittest.main()
