"""Plotting utilities for simulation results."""

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from vcm.core.models import SimulationResult


def plot_trajectory(
    result: SimulationResult,
    entity_id: str,
    entity_type: str,
    output_path: Optional[Path] = None,
    show: bool = False,
) -> None:
    """Plot time-series trajectory for a specific entity.

    Args:
        result: SimulationResult containing the trajectory
        entity_id: ID of the entity to plot
        entity_type: Type of entity (gene, protein, metabolite, pathway)
        output_path: Optional path to save the plot
        show: Whether to display the plot
    """
    trajectory = result.get_trajectory(entity_id, entity_type)
    timepoints = result.get_timepoints()

    plt.figure(figsize=(10, 6))
    plt.plot(timepoints, trajectory, linewidth=2, color="steelblue")
    plt.xlabel("Time", fontsize=12)
    plt.ylabel(f"{entity_type.capitalize()} Level", fontsize=12)
    plt.title(f"{entity_type.capitalize()} {entity_id} Over Time", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_state_comparison(
    result1: SimulationResult,
    result2: SimulationResult,
    entity_ids: Optional[List[str]] = None,
    entity_type: str = "gene",
    output_path: Optional[Path] = None,
    show: bool = False,
) -> None:
    """Compare states between two simulation results.

    Args:
        result1: First simulation result
        result2: Second simulation result
        entity_ids: List of entity IDs to compare (if None, uses all)
        entity_type: Type of entity to compare
        output_path: Optional path to save the plot
        show: Whether to display the plot
    """
    # Determine which entities to plot
    if entity_ids is None:
        # Use entities from first result
        if entity_type == "gene" and result1.final_state:
            entity_ids = list(result1.final_state.genes.keys())[:10]
        elif entity_type == "protein" and result1.final_state:
            entity_ids = list(result1.final_state.proteins.keys())[:10]
        elif entity_type == "metabolite" and result1.final_state:
            entity_ids = list(result1.final_state.metabolites.keys())[:10]
        else:
            entity_ids = []

    # Get final states
    state1 = result1.final_state
    state2 = result2.final_state

    if not state1 or not state2:
        raise ValueError("Both results must have final states")

    # Collect values
    values1 = []
    values2 = []
    labels = []

    for entity_id in entity_ids:
        if entity_type == "gene" and entity_id in state1.genes and entity_id in state2.genes:
            values1.append(state1.genes[entity_id].expression_level)
            values2.append(state2.genes[entity_id].expression_level)
            labels.append(entity_id)
        elif entity_type == "protein" and entity_id in state1.proteins and entity_id in state2.proteins:
            values1.append(state1.proteins[entity_id].concentration)
            values2.append(state2.proteins[entity_id].concentration)
            labels.append(entity_id)
        elif (
            entity_type == "metabolite"
            and entity_id in state1.metabolites
            and entity_id in state2.metabolites
        ):
            values1.append(state1.metabolites[entity_id].concentration)
            values2.append(state2.metabolites[entity_id].concentration)
            labels.append(entity_id)

    if not labels:
        raise ValueError(f"No matching {entity_type} entities found")

    # Create bar plot
    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    rects1 = ax.bar([i - width / 2 for i in x], values1, width, label="Result 1", color="steelblue")
    rects2 = ax.bar([i + width / 2 for i in x], values2, width, label="Result 2", color="coral")

    ax.set_xlabel(f"{entity_type.capitalize()} ID", fontsize=12)
    ax.set_ylabel(f"{entity_type.capitalize()} Level", fontsize=12)
    ax.set_title(f"{entity_type.capitalize()} Comparison Between Two Simulations", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_pathway_network(
    result: SimulationResult,
    pathway_id: str,
    output_path: Optional[Path] = None,
    show: bool = False,
) -> None:
    """Plot a pathway network graph.

    Args:
        result: SimulationResult containing pathway data
        pathway_id: ID of the pathway to visualize
        output_path: Optional path to save the plot
        show: Whether to display the plot
    """
    # Get pathway
    if not result.final_state or pathway_id not in result.final_state.pathways:
        raise ValueError(f"Pathway {pathway_id} not found in result")

    pathway = result.final_state.pathways[pathway_id]
    state = result.final_state

    # Create network graph
    G = nx.Graph()

    # Add pathway node
    G.add_node(pathway_id, node_type="pathway", size=pathway.flux * 500)

    # Add protein nodes
    for protein_id in pathway.proteins:
        if protein_id in state.proteins:
            G.add_node(
                protein_id,
                node_type="protein",
                size=state.proteins[protein_id].concentration * 300,
            )
            G.add_edge(pathway_id, protein_id)

    # Add metabolite nodes
    for metabolite_id in pathway.metabolites:
        if metabolite_id in state.metabolites:
            G.add_node(
                metabolite_id,
                node_type="metabolite",
                size=state.metabolites[metabolite_id].concentration * 200,
            )
            G.add_edge(pathway_id, metabolite_id)

    # Draw graph
    plt.figure(figsize=(12, 8))

    pos = nx.spring_layout(G, k=2, iterations=50)

    # Color nodes by type
    node_colors = []
    for node in G.nodes():
        node_type = G.nodes[node].get("node_type", "unknown")
        if node_type == "pathway":
            node_colors.append("#ff6b6b")
        elif node_type == "protein":
            node_colors.append("#4ecdc4")
        elif node_type == "metabolite":
            node_colors.append("#45b7d1")
        else:
            node_colors.append("#gray")

    node_sizes = [G.nodes[node].get("size", 300) for node in G.nodes()]

    nx.draw_networkx(
        G,
        pos,
        node_color=node_colors,
        node_size=node_sizes,
        with_labels=True,
        font_size=10,
        font_weight="bold",
        edge_color="gray",
        width=2,
        alpha=0.8,
    )

    plt.title(f"Pathway Network: {pathway.name}", fontsize=16)
    plt.axis("off")
    plt.tight_layout()

    # Add legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#ff6b6b", label="Pathway"),
        Patch(facecolor="#4ecdc4", label="Protein"),
        Patch(facecolor="#45b7d1", label="Metabolite"),
    ]
    plt.legend(handles=legend_elements, loc="upper right")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_multiple_trajectories(
    results: List[SimulationResult],
    entity_id: str,
    entity_type: str,
    labels: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
    show: bool = False,
) -> None:
    """Plot trajectories from multiple simulation results on the same plot.

    Args:
        results: List of SimulationResult objects
        entity_id: ID of the entity to plot
        entity_type: Type of entity (gene, protein, metabolite, pathway)
        labels: Optional labels for each result
        output_path: Optional path to save the plot
        show: Whether to display the plot
    """
    if labels is None:
        labels = [f"Result {i + 1}" for i in range(len(results))]

    plt.figure(figsize=(10, 6))

    colors = ["steelblue", "coral", "forestgreen", "purple", "orange"]

    for i, result in enumerate(results):
        trajectory = result.get_trajectory(entity_id, entity_type)
        timepoints = result.get_timepoints()
        color = colors[i % len(colors)]
        plt.plot(timepoints, trajectory, linewidth=2, color=color, label=labels[i])

    plt.xlabel("Time", fontsize=12)
    plt.ylabel(f"{entity_type.capitalize()} Level", fontsize=12)
    plt.title(f"{entity_type.capitalize()} {entity_id} Comparison", fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()
