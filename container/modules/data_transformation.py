"""
Custom rdetoolkit dataset function for the tensile-test (TTO) pipeline.

The ELN fetch runs in main.py before rdetoolkit starts, so the downloaded
files are already in inputdata (and therefore in resource_paths.rawfiles,
and copied to raw by rdetoolkit) when this function is called.

Per run:
  1. Pair every {process_id}_metadata.json with its {process_id}.csv
     from the input files.
  2. Per specimen write: a plain structured dump, an RDE-validated typed
     metadata record, the stress-strain time-series as CSV, and an
     ontology-mapped canonical JSON.
"""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rdetoolkit.models.rde2types import RdeInputDirPaths, RdeOutputResourcePath
from rdetoolkit.rde2util import Meta
from rdetoolkit.exceptions import StructuredError
from rdetoolkit.fileops import writef_json
from modules.jsontocjson_tto import transform_json_to_canonical


def read_tensile_csv(csv_path: Path) -> pd.DataFrame | None:
    """
    Reads a tensile-test CSV export: a tab-separated key/value header block,
    then the 'Time ...' column header, a unit row, and the measurement data.
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Find where measurement data starts
    try:
        skip_rows = next(i for i, line in enumerate(lines) if line.startswith("Time"))
    except StopIteration:
        print(f"Skipping {csv_path.name}: 'Time' column not found.")
        return None

    df = pd.read_csv(csv_path, sep='\t', skiprows=skip_rows)

    # Remove the unit row (s, mm, kN, ...) if present
    if not df.empty and pd.isna(pd.to_numeric(df.iloc[0, 0], errors='coerce')):
        df = df.drop(0).reset_index(drop=True)
    return df.apply(pd.to_numeric, errors='coerce')


def get_input_files(file_paths: list[Path]) -> list[tuple[str, dict, pd.DataFrame]]:
    """
    Groups files by process_id: every [process_id]_metadata.json is paired
    with its [process_id].csv. Returns a list of (process_id, metadata, dataframe).
    """
    results = []

    metadata_files = [f for f in file_paths if f.name.endswith("_metadata.json")]

    for meta_path in metadata_files:
        process_id = meta_path.name.removesuffix("_metadata.json")

        csv_path = next((f for f in file_paths if f.name == f"{process_id}.csv"), None)
        if csv_path is None:
            print(f"Skipping {process_id}: no matching {process_id}.csv found.")
            continue

        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        metadata.setdefault("process_id", process_id)

        df = read_tensile_csv(csv_path)
        if df is None:
            continue

        results.append((process_id, metadata, df))

    return results


def save_metadata(metadata: dict[str, str], metadata_def_json_path: str | Path, save_path: str | Path):
    """Saves metadata typed and validated according to metadata-def.json."""
    meta = Meta(metadata_def_json_path)
    meta.assign_vals(metadata)
    meta.writefile(str(save_path))


def tensile_plot(data: pd.DataFrame, output_path: str | Path):
    """Engineering stress-strain curve."""
    plt.figure(figsize=(10, 6))
    plt.plot(data['Engineering Strain'], data['Engineering Stress'], label='Measured Data', color='b')
    plt.xlabel('Engineering Strain [-]')
    plt.ylabel('Engineering Stress [MPa]')
    plt.title('Engineering Stress-Strain Curve')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def my_tto_func(srcpaths: RdeInputDirPaths, resource_paths: RdeOutputResourcePath):
    """rdetoolkit custom_dataset_function: processes every metadata/CSV
    pair from the input files and writes the four output artifacts
    described in the module docstring."""
    try:
        # 1. Pair the metadata/CSV files from inputdata
        all_experiments = get_input_files(resource_paths.rawfiles)

        if not all_experiments:
            print("No matching metadata/csv pairs found.")
            return

        metadata_def_path = srcpaths.tasksupport.joinpath("metadata-def.json")

        for process_id, metadata, dataframe in all_experiments:
            # 2. Save the plain metadata as [process_id].json in the 'struct' folder
            writef_json(resource_paths.struct.joinpath(f"{process_id}.json"), metadata)

            # 2b. Save the RDE-validated, typed metadata as [process_id]_metadata.json
            #     in the 'meta' folder
            try:
                meta_path = resource_paths.meta.joinpath(f"{process_id}_metadata.json")
                save_metadata(metadata, metadata_def_path, meta_path)
            except StructuredError as e:
                print(f"Error saving metadata for {process_id}: {e}")
                continue

            # 3. Save the measurement data as [process_id].csv in the 'struct' folder
            dataframe.to_csv(
                resource_paths.struct.joinpath(f"{process_id}.csv"),
                index=False
            )

            # 4. Save the ontology-mapped canonical JSON as [process_id]_canonical.json
            #    in the 'struct' folder, built from the just-written meta output
            transform_json_to_canonical(
                meta_path,
                metadata_def_path,
                resource_paths.struct.joinpath(f"{process_id}_canonical.json")
            )

            print(f"Processed and saved: {process_id}")

    except Exception as e:
        raise StructuredError(f"An error occurred during processing: {e}") from e
