"""Entry point for the tensile-test (TTO) rdetoolkit dataset structuring run."""
import rdetoolkit

from modules.data_transformation import my_tto_func
from modules.fetch_experiments_from_ELN import fetch_experiments

# 1. Fetch the RDE-flagged experiments from the ELN into inputdata first, so
#    rdetoolkit picks them up as input files and copies them to raw itself.
#    A missing/unreachable ELN is not fatal: files already in inputdata are
#    still processed.
try:
    downloaded = fetch_experiments("data/inputdata")
    print(f"Fetched {len(downloaded)} file(s) from ELN into data/inputdata")
except Exception as e:
    print(f"Warning: could not fetch experiments from ELN: {e}")

# 2. Run the RDE structuring pipeline on inputdata
rdetoolkit.workflows.run(custom_dataset_function=my_tto_func)
