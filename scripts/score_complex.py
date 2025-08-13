#!/usr/bin/env python3
import subprocess
import pandas as pd
from Bio.PDB import PDBParser, PDBIO, Structure, Model
from pathlib import Path
import os
import sys

def score_complex(pdb_path: str, ligand_chain: str, n_cores: int = os.cpu_count()) -> dict:
    app_dir = Path("/app")
    pdb_file = Path(pdb_path).resolve()

    if not pdb_file.exists():
        print(f"Error: PDB file '{pdb_file}' not found.")
        return {}

    ## Parse the PDB file to extract the ligand
    print("Parsing PDB file to extract ligand...") 
    ligand_pdb = app_dir / "ligand.pdb"
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein_structure", str(pdb_file))

    extracted_chain = None
    for model in structure:
        for chain in model:
            if chain.get_id().strip().upper() == ligand_chain:
                extracted_chain = chain
                break
        if extracted_chain:
            break

    if not extracted_chain:
        print(f"Chain '{ligand_chain}' not found in '{pdb_file.name}'")
        return {}
    
    # Wrap chain into new structure
    new_structure = Structure.Structure("ligand_only")
    new_model = Model.Model(0)
    new_model.add(extracted_chain.copy())
    new_structure.add(new_model)

    io = PDBIO()
    io.set_structure(new_structure)
    io.save(str(ligand_pdb))
    print(f"Chain '{ligand_chain}' extracted to '{ligand_pdb}'")


    ## Run ACPYPE on ligand to generate topology files
    print("Running ACPYPE...")
    try:
        subprocess.run(
            ["acpype", "-i", str(ligand_pdb), "-o", "cns"],
            capture_output=True, text=True, check=True, cwd=app_dir
        )
    except subprocess.CalledProcessError as e:
        print("ACPYPE Error:", e.stderr)
        return {}

    ## Create a configuration file for HADDOCK3 scoring
    cfg_body = f'''
    ## Docked protein complex scoring
    run_dir = "run0"
    mode = "local"
    ncores = {n_cores}
    molecules =  [
        "{pdb_file}"
        ]
    [topoaa]
    autohis = true
    ligand_param_fname = "{app_dir}/ligand.acpype/ligand_CNS.par"
    ligand_top_fname = "{app_dir}/ligand.acpype/ligand_CNS.top"
    [mdscoring]
    ligand_param_fname = "{app_dir}/ligand.acpype/ligand_CNS.par"
    ligand_top_fname = "{app_dir}/ligand.acpype/ligand_CNS.top"
    nemsteps = 1
    per_interface_scoring = false
    '''

    cfg_file = app_dir / "score.cfg"
    cfg_file.write_text(cfg_body.strip())

    ## Run HADDOCK3 scoring
    print("Running HADDOCK3 scoring...")
    try:
        subprocess.run(
            ["haddock3", str(cfg_file)],
            capture_output=True, text=True, check=True, cwd=app_dir
        )

        capri_file = app_dir / "run0/analysis/1_mdscoring_analysis/capri_ss.tsv"
        capri_ss = pd.read_csv(capri_file, sep="\t")
        metrics = capri_ss[['score', 'total', 'vdw', 'elec', 'desolv', 'bsa']].iloc[0].to_dict()

    except subprocess.CalledProcessError as e:
        print("HADDOCK3 Error:", e.stderr)
        return {}
    except Exception as e:
        print("Unexpected error:", e)
        return {}
    
    return metrics

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_complex.py <pdb_path> <ligand_chain> [n_cores]")
        sys.exit(1)

    pdb_path = sys.argv[1]
    ligand_chain = sys.argv[2].strip().upper()
    n_cores = int(sys.argv[3]) if len(sys.argv) > 3 else os.cpu_count()

    metrics = score_complex(pdb_path, ligand_chain, n_cores)
    if metrics:
        print("Scoring metrics:", metrics)
    else:
        print("Failed to score the complex.")