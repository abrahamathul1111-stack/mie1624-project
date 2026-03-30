"""KPI gap-attribution exports for policy recommendation scenarios."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.simulation.state_transition import COUNTRY_CLUSTER_MAP, SCENARIO_DEFINITIONS


DEFAULT_BASELINE_KPI_PATH = Path("outputs") / "tables" / "baseline_kpi_scores.csv"
DEFAULT_CANADA_TRAJECTORY_PATH = Path("outputs") / "tables" / "canada_kpi_trajectories.csv"
DEFAULT_TABLES_OUTPUT_DIR = Path("outputs") / "tables"
DEFAULT_FIGURES_OUTPUT_DIR = Path("outputs") / "figures"
DEFAULT_CANADA_COUNTRY = "Canada"

SCENARIO_EXPORT_ORDER = ["rec1_only", "rec2_only", "rec3_only", "all_recommendations"]
SCENARIO_LABELS = {
    "rec1_only": "Rec 1 Only",
    "rec2_only": "Rec 2 Only",
    "rec3_only": "Rec 3 Only",
    "all_recommendations": "All Recs",
}
BENCHMARK_LABELS = {
    "peer_best": "Peer-Cluster Best",
    "global_best": "Global Best",
}


class RecommendationAttributionError(ValueError):
    """Raised when attribution inputs cannot be aligned safely."""


def _validate_columns(frame: pd.DataFrame, required: list[str], name: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise RecommendationAttributionError(f"{name} is missing required columns: {missing}")


def _resolve(path_like: str | Path) -> Path:
    return Path(path_like).expanduser().resolve()


def _safe_gap(best_score: float, score: float) -> float:
    return max(float(best_score) - float(score), 0.0)


def _clean_for_filename(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def build_kpi_benchmarks(
    baseline_kpi_scores: pd.DataFrame,
    canada_country: str = DEFAULT_CANADA_COUNTRY,
) -> pd.DataFrame:
    """Build baseline KPI benchmark anchors for peer-cluster best and global best."""

    _validate_columns(
        baseline_kpi_scores,
        ["country", "kpi_order", "pillar", "subpillar", "kpi", "kpi_score"],
        "baseline_kpi_scores",
    )

    if canada_country not in set(baseline_kpi_scores["country"]):
        raise RecommendationAttributionError(
            f"Canada country key '{canada_country}' was not found in baseline_kpi_scores."
        )

    canada_cluster = COUNTRY_CLUSTER_MAP.get(canada_country)
    if canada_cluster is None:
        raise RecommendationAttributionError(
            f"No cluster mapping is defined for Canada country key '{canada_country}'."
        )

    baseline = baseline_kpi_scores.copy()
    baseline["kpi_score"] = pd.to_numeric(baseline["kpi_score"], errors="raise")
    baseline["cluster"] = baseline["country"].map(COUNTRY_CLUSTER_MAP)

    if baseline["cluster"].isna().any():
        missing = sorted(set(baseline.loc[baseline["cluster"].isna(), "country"]))
        raise RecommendationAttributionError(
            f"Missing cluster mapping for countries in baseline_kpi_scores: {missing}"
        )

    peer_pool = baseline.loc[
        (baseline["cluster"] == canada_cluster) & (baseline["country"] != canada_country)
    ].copy()
    if peer_pool.empty:
        peer_pool = baseline.loc[baseline["cluster"] == canada_cluster].copy()

    global_best_idx = baseline.groupby("kpi")["kpi_score"].idxmax()
    global_best = baseline.loc[
        global_best_idx,
        ["kpi", "country", "kpi_score"],
    ].rename(
        columns={
            "country": "global_best_country",
            "kpi_score": "global_best_score",
        }
    )

    peer_best_idx = peer_pool.groupby("kpi")["kpi_score"].idxmax()
    peer_best = peer_pool.loc[
        peer_best_idx,
        ["kpi", "country", "kpi_score"],
    ].rename(
        columns={
            "country": "peer_best_country",
            "kpi_score": "peer_best_score",
        }
    )

    benchmark = peer_best.merge(global_best, on="kpi", how="outer")

    metadata = (
        baseline[["kpi_order", "pillar", "subpillar", "kpi"]]
        .drop_duplicates()
        .sort_values("kpi_order")
    )
    benchmark = metadata.merge(benchmark, on="kpi", how="left")

    canada_baseline = baseline.loc[baseline["country"] == canada_country, ["kpi", "kpi_score"]].rename(
        columns={"kpi_score": "baseline_canada_score"}
    )
    benchmark = benchmark.merge(canada_baseline, on="kpi", how="left")
    if benchmark["baseline_canada_score"].isna().any():
        missing_kpis = benchmark.loc[benchmark["baseline_canada_score"].isna(), "kpi"].tolist()
        raise RecommendationAttributionError(
            f"Missing Canada baseline KPI score(s): {missing_kpis}"
        )

    for col in ["peer_best_score", "global_best_score"]:
        benchmark[col] = pd.to_numeric(benchmark[col], errors="raise")

    benchmark["baseline_gap_peer_best"] = benchmark.apply(
        lambda row: _safe_gap(row["peer_best_score"], row["baseline_canada_score"]),
        axis=1,
    )
    benchmark["baseline_gap_global_best"] = benchmark.apply(
        lambda row: _safe_gap(row["global_best_score"], row["baseline_canada_score"]),
        axis=1,
    )

    return benchmark.sort_values("kpi_order").reset_index(drop=True)


def build_gap_reduction_frame(
    benchmark_frame: pd.DataFrame,
    canada_kpi_trajectories: pd.DataFrame,
) -> pd.DataFrame:
    """Compute scenario-level post-policy gap and gap-reduction metrics per KPI."""

    _validate_columns(
        canada_kpi_trajectories,
        ["scenario", "quarter_index", "kpi", "kpi_score_median"],
        "canada_kpi_trajectories",
    )

    scenario_trajectories = canada_kpi_trajectories.copy()
    scenario_trajectories["kpi_score_median"] = pd.to_numeric(
        scenario_trajectories["kpi_score_median"],
        errors="raise",
    )

    final_quarter = int(scenario_trajectories["quarter_index"].max())
    latest = scenario_trajectories.loc[
        scenario_trajectories["quarter_index"] == final_quarter,
        ["scenario", "kpi", "kpi_score_median"],
    ].rename(columns={"kpi_score_median": "scenario_canada_score"})

    required_scenarios = list(SCENARIO_DEFINITIONS)
    missing_scenarios = sorted(set(required_scenarios) - set(latest["scenario"]))
    if missing_scenarios:
        raise RecommendationAttributionError(
            f"canada_kpi_trajectories is missing scenario(s): {missing_scenarios}"
        )

    if latest.groupby(["scenario", "kpi"]).size().gt(1).any():
        raise RecommendationAttributionError(
            "canada_kpi_trajectories has duplicate rows for (scenario, kpi) at final quarter."
        )

    joined = latest.merge(benchmark_frame, on="kpi", how="left")
    if joined[["kpi_order", "baseline_canada_score"]].isna().any().any():
        raise RecommendationAttributionError(
            "Scenario KPI rows could not be aligned with the benchmark frame."
        )

    rows: list[dict[str, object]] = []
    for row in joined.to_dict("records"):
        for benchmark_type in ["peer_best", "global_best"]:
            best_score = float(row[f"{benchmark_type}_score"])
            baseline_gap = float(row[f"baseline_gap_{benchmark_type}"])
            post_policy_gap = _safe_gap(best_score, float(row["scenario_canada_score"]))
            gap_reduction = baseline_gap - post_policy_gap
            percent_reduction = (gap_reduction / baseline_gap * 100.0) if baseline_gap > 0 else 0.0

            rows.append(
                {
                    "scenario": row["scenario"],
                    "quarter_index": final_quarter,
                    "kpi_order": int(row["kpi_order"]),
                    "pillar": row["pillar"],
                    "subpillar": row["subpillar"],
                    "kpi": row["kpi"],
                    "benchmark_type": benchmark_type,
                    "benchmark_label": BENCHMARK_LABELS[benchmark_type],
                    "benchmark_country": row[f"{benchmark_type}_country"],
                    "benchmark_score": best_score,
                    "baseline_canada_score": float(row["baseline_canada_score"]),
                    "scenario_canada_score": float(row["scenario_canada_score"]),
                    "baseline_gap": baseline_gap,
                    "post_policy_gap": post_policy_gap,
                    "absolute_gap_reduction": gap_reduction,
                    "percent_gap_reduction": percent_reduction,
                }
            )

    result = pd.DataFrame(rows)
    scenario_sort = {name: idx for idx, name in enumerate(SCENARIO_DEFINITIONS)}
    result["scenario_sort"] = result["scenario"].map(scenario_sort)
    result = result.sort_values(
        ["scenario_sort", "benchmark_type", "kpi_order"],
    ).drop(columns=["scenario_sort"])
    return result.reset_index(drop=True)


def _format_kpi_label(frame: pd.DataFrame) -> pd.Series:
    return frame["kpi_order"].astype(str).str.zfill(2) + " - " + frame["kpi"]


def _plot_heatmap(gap_reduction_by_recommendation: pd.DataFrame, output_path: Path) -> None:
    heatmap_source = gap_reduction_by_recommendation.loc[
        gap_reduction_by_recommendation["benchmark_type"] == "global_best"
    ].copy()
    heatmap_source["scenario"] = pd.Categorical(
        heatmap_source["scenario"],
        categories=SCENARIO_EXPORT_ORDER,
        ordered=True,
    )
    heatmap_source = heatmap_source.sort_values(["kpi_order", "scenario"])
    heatmap_source["kpi_label"] = _format_kpi_label(heatmap_source)

    pivot = heatmap_source.pivot_table(
        index="kpi_label",
        columns="scenario",
        values="percent_gap_reduction",
        aggfunc="mean",
    ).reindex(columns=SCENARIO_EXPORT_ORDER)

    plt.rcParams.update(
        {
            "figure.facecolor": "#f8f7f3",
            "axes.facecolor": "#f8f7f3",
            "font.family": "DejaVu Sans",
        }
    )
    fig, ax = plt.subplots(figsize=(13.5, 11.5), dpi=180)
    image = ax.imshow(pivot.to_numpy(), cmap="YlGnBu", aspect="auto")

    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([SCENARIO_LABELS.get(col, col) for col in pivot.columns], fontsize=11)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index.tolist(), fontsize=8.3)

    ax.set_title(
        "Recommendation Impact by KPI\nPercent Gap Reduction vs Global Best (Final Quarter)",
        fontsize=16,
        weight="bold",
        pad=16,
    )
    ax.set_xlabel("Scenario", fontsize=12, labelpad=8)
    ax.set_ylabel("KPI", fontsize=12, labelpad=8)

    for row_idx in range(pivot.shape[0]):
        for col_idx in range(pivot.shape[1]):
            value = pivot.iat[row_idx, col_idx]
            if np.isnan(value):
                label = "-"
                text_color = "#4b5563"
            else:
                label = f"{value:.1f}%"
                text_color = "#0f172a" if value < 55 else "#ffffff"
            ax.text(col_idx, row_idx, label, ha="center", va="center", color=text_color, fontsize=7.8)

    cbar = fig.colorbar(image, ax=ax, fraction=0.032, pad=0.03)
    cbar.set_label("Percent gap reduction", fontsize=11)
    cbar.ax.tick_params(labelsize=9)

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _plot_scenario_gap_reduction(
    gap_reduction_by_recommendation: pd.DataFrame,
    scenario: str,
    output_path: Path,
) -> None:
    scenario_frame = gap_reduction_by_recommendation.loc[
        gap_reduction_by_recommendation["scenario"] == scenario
    ].copy()
    if scenario_frame.empty:
        raise RecommendationAttributionError(f"No rows found for scenario '{scenario}'.")

    scenario_frame = scenario_frame[["kpi_order", "kpi", "benchmark_type", "absolute_gap_reduction"]]
    pivot = scenario_frame.pivot_table(
        index=["kpi_order", "kpi"],
        columns="benchmark_type",
        values="absolute_gap_reduction",
        aggfunc="mean",
    ).reset_index()
    for col in ["peer_best", "global_best"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
    pivot = pivot.sort_values(["global_best", "peer_best"], ascending=[False, False]).reset_index(drop=True)

    y = np.arange(len(pivot))
    labels = pivot["kpi_order"].astype(str).str.zfill(2) + " " + pivot["kpi"]

    plt.rcParams.update(
        {
            "figure.facecolor": "#f8f7f3",
            "axes.facecolor": "#f8f7f3",
            "font.family": "DejaVu Sans",
        }
    )
    fig, ax = plt.subplots(figsize=(14.5, 11.5), dpi=180)

    bar_height = 0.38
    ax.barh(
        y - (bar_height / 2),
        pivot["peer_best"],
        height=bar_height,
        color="#3b82f6",
        label=BENCHMARK_LABELS["peer_best"],
        alpha=0.90,
    )
    ax.barh(
        y + (bar_height / 2),
        pivot["global_best"],
        height=bar_height,
        color="#f59e0b",
        label=BENCHMARK_LABELS["global_best"],
        alpha=0.90,
    )

    ax.axvline(0.0, color="#1f2937", linewidth=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.3)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.35, color="#9ca3af")

    scenario_title = SCENARIO_LABELS.get(scenario, scenario)
    ax.set_title(
        f"{scenario_title}: KPI Gap Reduction by Benchmark\nAbsolute Reduction (Final Quarter)",
        fontsize=16,
        weight="bold",
        pad=14,
    )
    ax.set_xlabel("Absolute gap reduction (points)", fontsize=12)
    ax.set_ylabel("KPI", fontsize=12)
    ax.legend(loc="lower right", frameon=False, fontsize=10)

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def export_recommendation_attribution(
    baseline_kpi_path: str | Path = DEFAULT_BASELINE_KPI_PATH,
    canada_trajectory_path: str | Path = DEFAULT_CANADA_TRAJECTORY_PATH,
    tables_output_dir: str | Path = DEFAULT_TABLES_OUTPUT_DIR,
    figures_output_dir: str | Path = DEFAULT_FIGURES_OUTPUT_DIR,
    canada_country: str = DEFAULT_CANADA_COUNTRY,
) -> dict[str, Path]:
    """Compute recommendation KPI gap attribution and export CSV + chart artifacts."""

    baseline_path = _resolve(baseline_kpi_path)
    trajectory_path = _resolve(canada_trajectory_path)
    tables_dir = _resolve(tables_output_dir)
    figures_dir = _resolve(figures_output_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    baseline_kpi_scores = pd.read_csv(baseline_path)
    canada_kpi_trajectories = pd.read_csv(trajectory_path)

    benchmark_frame = build_kpi_benchmarks(
        baseline_kpi_scores=baseline_kpi_scores,
        canada_country=canada_country,
    )
    gap_reduction_all = build_gap_reduction_frame(
        benchmark_frame=benchmark_frame,
        canada_kpi_trajectories=canada_kpi_trajectories,
    )

    gap_reduction_by_recommendation = gap_reduction_all.loc[
        gap_reduction_all["scenario"].isin(SCENARIO_EXPORT_ORDER)
    ].copy()
    gap_reduction_by_recommendation["scenario"] = pd.Categorical(
        gap_reduction_by_recommendation["scenario"],
        categories=SCENARIO_EXPORT_ORDER,
        ordered=True,
    )
    gap_reduction_by_recommendation = gap_reduction_by_recommendation.sort_values(
        ["scenario", "benchmark_type", "kpi_order"]
    )

    peer_best_frame = gap_reduction_by_recommendation.loc[
        gap_reduction_by_recommendation["benchmark_type"] == "peer_best"
    ].copy()
    global_best_frame = gap_reduction_by_recommendation.loc[
        gap_reduction_by_recommendation["benchmark_type"] == "global_best"
    ].copy()

    output_paths = {
        "kpi_gap_reduction_by_recommendation": tables_dir / "kpi_gap_reduction_by_recommendation.csv",
        "kpi_gap_reduction_peer_best": tables_dir / "kpi_gap_reduction_peer_best.csv",
        "kpi_gap_reduction_global_best": tables_dir / "kpi_gap_reduction_global_best.csv",
        "recommendation_kpi_heatmap": figures_dir / "recommendation_kpi_heatmap.png",
        "rec1_gap_reduction": figures_dir / "rec1_gap_reduction.png",
        "rec2_gap_reduction": figures_dir / "rec2_gap_reduction.png",
        "rec3_gap_reduction": figures_dir / "rec3_gap_reduction.png",
        "combined_gap_reduction": figures_dir / "combined_gap_reduction.png",
    }

    gap_reduction_by_recommendation.to_csv(
        output_paths["kpi_gap_reduction_by_recommendation"],
        index=False,
    )
    peer_best_frame.to_csv(output_paths["kpi_gap_reduction_peer_best"], index=False)
    global_best_frame.to_csv(output_paths["kpi_gap_reduction_global_best"], index=False)

    _plot_heatmap(
        gap_reduction_by_recommendation=gap_reduction_by_recommendation,
        output_path=output_paths["recommendation_kpi_heatmap"],
    )
    _plot_scenario_gap_reduction(
        gap_reduction_by_recommendation=gap_reduction_by_recommendation,
        scenario="rec1_only",
        output_path=output_paths["rec1_gap_reduction"],
    )
    _plot_scenario_gap_reduction(
        gap_reduction_by_recommendation=gap_reduction_by_recommendation,
        scenario="rec2_only",
        output_path=output_paths["rec2_gap_reduction"],
    )
    _plot_scenario_gap_reduction(
        gap_reduction_by_recommendation=gap_reduction_by_recommendation,
        scenario="rec3_only",
        output_path=output_paths["rec3_gap_reduction"],
    )
    _plot_scenario_gap_reduction(
        gap_reduction_by_recommendation=gap_reduction_by_recommendation,
        scenario="all_recommendations",
        output_path=output_paths["combined_gap_reduction"],
    )

    return output_paths


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for recommendation gap attribution exports."""

    parser = argparse.ArgumentParser(
        description="Export KPI gap-reduction attribution tables and charts for recommendation scenarios."
    )
    parser.add_argument(
        "--baseline-kpis",
        default=str(DEFAULT_BASELINE_KPI_PATH),
        help="Path to baseline_kpi_scores.csv.",
    )
    parser.add_argument(
        "--canada-trajectories",
        default=str(DEFAULT_CANADA_TRAJECTORY_PATH),
        help="Path to canada_kpi_trajectories.csv.",
    )
    parser.add_argument(
        "--tables-output-dir",
        default=str(DEFAULT_TABLES_OUTPUT_DIR),
        help="Directory for CSV exports.",
    )
    parser.add_argument(
        "--figures-output-dir",
        default=str(DEFAULT_FIGURES_OUTPUT_DIR),
        help="Directory for chart PNG exports.",
    )
    parser.add_argument(
        "--canada-country",
        default=DEFAULT_CANADA_COUNTRY,
        help="Country label used to identify Canada in baseline KPI inputs.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for recommendation impact attribution exports."""

    parser = build_argument_parser()
    args = parser.parse_args()
    output_paths = export_recommendation_attribution(
        baseline_kpi_path=args.baseline_kpis,
        canada_trajectory_path=args.canada_trajectories,
        tables_output_dir=args.tables_output_dir,
        figures_output_dir=args.figures_output_dir,
        canada_country=args.canada_country,
    )
    for key, value in output_paths.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
