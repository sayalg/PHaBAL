# Base image with conda
FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Install system dependencies for haddock3/freesasa build
RUN apt-get update && \
    apt-get install -y build-essential libxml2-dev libgsl-dev && \
    rm -rf /var/lib/apt/lists/*

# Create and activate conda env with Python 3.9
RUN conda create -n ligandbind_env python=3.9 -y && \
    conda clean --all -f -y

# Install dependencies inside the env
RUN conda run -n ligandbind_env conda install -c conda-forge acpype && \
    conda run -n ligandbind_env pip install haddock3 pandas biopython

# Copy your Python script into the container
COPY scripts/ /app/scripts/

# Ensure conda env is used by default
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "ligandbind_env", "python", "/app/scripts/score_complex.py"]
