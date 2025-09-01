# Predictin HADDOCK Binding Affinity for Ligands (PHaBAL)

We are creating a docker container that will house ACPYPE and HADDOCK3. The purpose of the container will be to run the phsyics based molecular dynamics simulations of HADDOCK3 to produce the binding affinity metrics (Van der Waals, Electrostatic Energy, etc.) for any provided docked structure of a protein and small molecule ligand. 

## Create docker image
docker build -t ligandbind .

## Run docker image
Example:
docker run -v "$(pwd):/mnt" ligandbind /mnt/example.pdb B

## Notes
If protein and ligand are labeled on the same chain, you can do the following:
1. Open PDB in PyMol
2. Select the ligand molecule
3. Enter command "alter (sele), chain='B'"
4. Export Structure -> Export Molecule