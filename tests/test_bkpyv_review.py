"""Guardrails for the reviewable BKPyV output layer."""
import json
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from pathlib import Path

from vcm.plugins.transplant.bk_polyomavirus import BKPolyomavirusPlugin


def test_nccr_scenarios_are_explicit_and_reviewable():
    plugin = BKPolyomavirusPlugin()
    archetype = plugin.create_initial_state({"nccr_variant": "archetype"})
    rearranged = plugin.create_initial_state({"nccr_variant": "rearranged"})

    assert archetype.metadata["nccr_variant"] == "archetype"
    assert rearranged.metadata["nccr_variant"] == "rearranged"
    assert "nccr_variants" in plugin.get_cell_schema()
    assert "rearranged" in plugin.get_cell_schema()["nccr_variants"]


def test_review_bundle_module_exports_builder():
    from vcm.viz.bkpyv_review import build_review_bundle

    assert callable(build_review_bundle)


def _fake_result():
    state = SimpleNamespace(
        metadata={
            "nccr_variant": "archetype",
            "viral_load": 0.2,
            "t_antigen_level": 0.4,
            "pathway_activities": {"dna_replication": 0.3, "cell_cycle": 0.6},
            "intracellular_replication_flux": 0.1,
            "viral_production_rate": 0.05,
            "immune_control_index": 0.8,
            "infection_status": "infected",
        },
        genes={},
    )
    return SimpleNamespace(steps=[SimpleNamespace(timestamp=0.0, cell_state=state)])


def test_trajectory_frame_has_schema_for_empty_result():
    from vcm.viz import bkpyv_review

    frame = bkpyv_review._trajectory_frame(SimpleNamespace(steps=[]), "empty")

    assert frame.empty
    assert "plasma_copies_per_ml" in frame.columns
    assert "vp1_capsid_expression" in frame.columns


def test_trajectory_frame_defaults_missing_state_fields():
    from vcm.viz import bkpyv_review

    result = SimpleNamespace(
        steps=[
            SimpleNamespace(
                timestamp=1.0,
                cell_state=SimpleNamespace(metadata={}, genes={}),
            )
        ]
    )
    with patch.object(bkpyv_review, "ViralLoadMapper") as mapper:
        mapper.return_value.normalized_to_copies.return_value = 0.0
        frame = bkpyv_review._trajectory_frame(result, "missing")

    assert frame.iloc[0]["virtual_viral_load"] == 0.0
    assert frame.iloc[0]["vp1_capsid_expression"] == 0.0
    assert frame.iloc[0]["infection_status"] == "uninfected"


def test_scenario_result_passes_reproducible_solver_settings():
    from vcm.viz import bkpyv_review

    captured = {}

    class FakeSimulator:
        def __init__(self, config):
            captured["config"] = config

        def simulate(self, initial_state, **kwargs):
            captured["kwargs"] = kwargs
            return _fake_result()

    with patch.object(bkpyv_review, "BKPyVODESimulator", FakeSimulator):
        bkpyv_review._scenario_result("archetype", days=2.0, timestep=0.5)

    assert captured["config"]["ode_solver"] == "LSODA"
    assert captured["config"]["rtol"] == 1e-6
    assert captured["config"]["atol"] == 1e-8
    assert captured["config"]["max_step"] == 0.5
    assert captured["kwargs"]["n_steps"] == 4


def test_scenario_result_encodes_tacrolimus_as_immune_control_target():
    from vcm.viz import bkpyv_review

    class FakeSimulator:
        def __init__(self, config):
            pass

        def simulate(self, initial_state, perturbations, **kwargs):
            assert perturbations[-1].target_id == "FKBP1A"
            return _fake_result()

    with patch.object(bkpyv_review, "BKPyVODESimulator", FakeSimulator):
        bkpyv_review._scenario_result("archetype", drug="tacrolimus", days=1.0)


def test_scenario_result_encodes_sirolimus_as_mtor_target():
    from vcm.viz import bkpyv_review

    class FakeSimulator:
        def __init__(self, config):
            pass

        def simulate(self, initial_state, perturbations, **kwargs):
            assert perturbations[-1].target_id == "MTOR"
            return _fake_result()

    with patch.object(bkpyv_review, "BKPyVODESimulator", FakeSimulator):
        bkpyv_review._scenario_result("archetype", drug="sirolimus", days=1.0)


def test_plot_functions_reject_empty_inputs():
    from vcm.viz import bkpyv_review

    empty = pd.DataFrame()
    with patch.object(bkpyv_review.plt, "close"):
        try:
            bkpyv_review.plot_mechanistic_trajectory(empty, "unused.png")
        except ValueError as exc:
            assert "empty" in str(exc)
        else:
            raise AssertionError("empty trajectory should be rejected")

    with patch.object(bkpyv_review.plt, "close"):
        try:
            bkpyv_review.plot_sensitivity_heatmap(empty, "unused.png")
        except ValueError as exc:
            assert "at least one" in str(exc)
        else:
            raise AssertionError("empty sensitivity table should be rejected")


def test_review_manifest_records_solver_and_interpretation_metadata(tmp_path):
    from vcm.viz import bkpyv_review

    sensitivity = pd.DataFrame(
        [{"parameter": "demo", "value": 1.0, "peak_production_rate": 0.2}]
    )

    def write_sensitivity(_variant, output_dir, _days=None, **kwargs):
        sensitivity.to_csv(output_dir / "sensitivity_results.csv", index=False)
        return sensitivity

    with patch.object(bkpyv_review, "_scenario_result", return_value=_fake_result()), patch.object(
        bkpyv_review, "ViralLoadMapper"
    ) as mapper, patch.object(bkpyv_review, "_sensitivity_table", side_effect=write_sensitivity), patch.object(
        bkpyv_review, "plot_mechanistic_trajectory"
    ), patch.object(bkpyv_review, "plot_nccr_comparison"), patch.object(
        bkpyv_review, "plot_drug_mechanisms"
    ), patch.object(bkpyv_review, "plot_sensitivity_heatmap"):
        mapper.return_value.normalized_to_copies.return_value = 20.0
        paths = bkpyv_review.build_review_bundle(tmp_path, days=3.0)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert paths["manifest"].endswith("manifest.json")
    assert manifest["ode_solver"] == "LSODA"
    assert manifest["rtol"] == 1e-6
    assert manifest["atol"] == 1e-8
    assert manifest["days"] == 3.0
    assert manifest["timestep"] == 1.0
    assert manifest["nccr_variant"] == ["archetype", "rearranged"]
    assert manifest["interpretation_caveats"]
