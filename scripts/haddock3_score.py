import re
import subprocess

def haddock3_score(pdb_path:str) -> dict:

  try:
    ## Run haddock3-score CLI
    command = ["haddock3-score", "--full", pdb_path]
    sp_result = subprocess.run(command, capture_output=True, text=True, check=True)

    ## Parse result
    metrics = {}

    ## Extract HADDOCK score
    match = re.search(r"HADDOCK-score \(emscoring\) = ([\-\d\.]+)", sp_result.stdout)
    if match:
        metrics["score"] = float(match.group(1))

    ## Extract individual energy terms
    matches = re.findall(r"(\w+)=([\-\d\.]+)", sp_result.stdout)
    for key, value in matches:
        metrics[key] = float(value)

    ## Calculate total score
    metrics["total"] = metrics["vdw"] + metrics["elec"]

    ## Remove air
    del metrics["air"]

    return metrics

  except subprocess.CalledProcessError as e:
    print("HADDOCK3 Error occurred:", e.stderr)
    return {}