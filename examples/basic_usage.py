"""
Basic example of using VCM Python API.

This script demonstrates how to:
1. Load a plugin
2. Create initial state
3. Configure an experiment
4. Run a simulation
5. Visualize results
"""

from pathlib import Path

from vcm.plugins.bacteria.minimal_cell import MinimalCellPlugin
from vcm.plugins.base import PluginRegistry
from vcm.simulators.mechanistic import MechanisticSimulator
from vcm.core.models import ExperimentConfig, Perturbation, PerturbationType, Environment
from vcm.experiments.runner import ExperimentRunner
from vcm.viz.plots import plot_trajectory

# Register plugin
plugin = MinimalCellPlugin()
plugin.register()

# Create initial state
initial_state = plugin.create_initial_state()
print(f"Created initial state for: {initial_state.cell_type}")
print(f"Number of genes: {len(initial_state.genes)}")
print(f"Number of proteins: {len(initial_state.proteins)}")
print(f"Number of metabolites: {len(initial_state.metabolites)}")
print()

# Configure experiment
config = ExperimentConfig(
    experiment_id="basic_example",
    plugin=plugin.plugin_id,
    simulator="mechanistic",
    simulation_length=50.0,
    timestep=0.5,
    output_path="outputs/basic_example/",
    environment=Environment(temperature=37.0, ph=7.4),
    perturbations=[],  # No perturbations for baseline
)

# Run experiment
print("Running simulation...")
runner = ExperimentRunner()
result = runner.run_experiment(config, initial_state)
print(f"Simulation complete: {len(result.steps)} steps")
print(f"Success: {result.success}")
print()

# Save results
runner.save_result(result, Path(config.output_path))
print(f"Results saved to: {config.output_path}")
print()

# Visualize trajectory for a specific gene
if result.final_state and "dnaA" in result.final_state.genes:
    print("Plotting dnaA gene expression trajectory...")
    plot_path = Path(config.output_path) / "dnaA_trajectory.png"
    plot_trajectory(
        result,
        entity_id="dnaA",
        entity_type="gene",
        output_path=plot_path,
        show=False,
    )
    print(f"Plot saved to: {plot_path}")

print("\nExample complete!")
