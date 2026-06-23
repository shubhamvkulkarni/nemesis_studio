#!/bin/bash
# Activate the conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nemesis_studio

# Run the backend server
python server.py
