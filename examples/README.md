# VCM Examples

This directory contains example scripts demonstrating how to use the VCM Python API.

## Examples

### basic_usage.py
Demonstrates the basic workflow:
- Loading a plugin
- Creating initial state
- Configuring an experiment
- Running a simulation
- Visualizing results

### Running the Examples

Make sure you have the VCM package installed and in your PYTHONPATH:

```bash
cd virtual-cell-model
export PYTHONPATH="/path/to/virtual-cell-model/src:$PYTHONPATH"
python examples/basic_usage.py
```

### Creating Your Own Examples

1. Copy `basic_usage.py` as a template
2. Modify the plugin, perturbations, and parameters
3. Add your own visualizations or analysis
4. Save your results and document your findings
