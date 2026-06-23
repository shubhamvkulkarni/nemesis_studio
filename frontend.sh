#!/bin/bash
# Activate the conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nemesis_studio

# Run the frontend server
panel serve frontend.py --show
