# Use a base image with Python 3 already installed
FROM acpype/acpype:latest

# Set the working directory inside the container
WORKDIR /app

# Install Python libraries
RUN pip install haddock3 pandas

# Copy scripts into container
COPY scripts/ /app/scripts/

# Run python script for protein-ligand binding affinity prediction
CMD ["python", "scripts/score_complex.py"]