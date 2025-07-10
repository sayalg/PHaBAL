import shutil
import subprocess
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

def score_complex(pdb_path: str, n_cores: int = os.cpu_count()) -> dict:
    pdb_file = Path(pdb_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        shutil.copy(pdb_file, temp_path)
        complex_pdb = pdb_file.name

        ## Extract ligand from the PDB file
        print("Extracting ligand from PDB file...")
        ligand_pdb = temp_path / "ligand.pdb"
        with open(temp_path / complex_pdb) as infile, open(ligand_pdb, "w") as outfile:
            for line in infile:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    if line[21] == "B":
                        outfile.write(line)

        ## Run ACPYPE on ligand to generate topology files
        print("Running ACPYPE to generate ligand topology files...")
        command = ["acpype", "-i", ligand_pdb, "-o," "cns"]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_path)
        except subprocess.CalledProcessError as e:
            print("ACPYPE Error occurred:", e.stderr)
            return {}

        ## Create a configuration file for HADDOCK3 scoring
        cfg_body = f'''
        ## Docked protein complex scoring
        run_dir = "run0"
        mode = "local"
        ncores = {n_cores}
        molecules =  [
            "{complex_pdb}"
            ]
        [topoaa]
        autohis = true
        ligand_param_fname = f"{temp_path}/ligand.acpype/ligand_CNS.par"
        ligand_top_fname = f"{temp_path}/ligand.acpype/ligand_CNS.top"
        [mdscoring]
        ligand_param_fname = f"{temp_path}/ligand.acpype/ligand_CNS.par"
        ligand_top_fname = f"{temp_path}/ligand.acpype/ligand_CNS.top"
        nemsteps = 1
        per_interface_scoring = false
        '''

        cfg_file = temp_path / "score.cfg"
        cfg_file.write_text(cfg_body.strip())

        ## Run HADDOCK3 scoring
        print("Running HADDOCK3 scoring...")
        try:
            command = ["haddock3", str(cfg_file)]
            subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_path)

            capri_file = temp_path / "run0/analysis/1_mdscoring_analysis/capri_ss.tsv"
            capri_ss = pd.read_csv(capri_file, sep="\t")
            metrics = capri_ss[['score', 'total', 'vdw', 'elec', 'desolv', 'bsa']].iloc[0].to_dict()
            return metrics

        except subprocess.CalledProcessError as e:
            print("HADDOCK3 Error occurred:", e.stderr)
            return {}

        except Exception as e:
            print("Unexpected error:", e)
            return {}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_complex.py <pdb_path> [n_cores]")
        sys.exit(1)

    pdb_path = sys.argv[1]
    n_cores = int(sys.argv[2]) if len(sys.argv) > 2 else os.cpu_count()

    metrics = score_complex(pdb_path, n_cores)
    if metrics:
        print("Scoring metrics:", metrics)
    else:
        print("Failed to score the complex.")