# rde-tto

An [RDE Toolkit](https://github.com/nims-mdpf/rdetoolkit) (NIMS's Research Data Express structuring framework) pipeline for tensile-test data — pulling tensile-test experiments from an eLabFTW electronic lab notebook, structuring them into RDE-standard metadata, and mapping that metadata onto a Tensile Test Ontology / PMD Core Ontology-style semantic graph.

Sister project of [rde-hto](https://github.com/gosula-materialdigital/RDE_HTO) (heat treatment), following the same structure.

## What it does

Each run of the pipeline:

1. **Fetches** every eLabFTW experiment titled `Tensile-test-ontology` whose extra field `RDE` is `true`: the key/value tables in the experiment body become `{process_id}_metadata.json`, the attached measurement file becomes `{process_id}.csv`. Both are written to `data/inputdata/`. This runs in `main.py` *before* rdetoolkit starts, so rdetoolkit treats the downloads as normal input files (and copies them to `data/raw/` itself).
2. **Pairs** every `{process_id}_metadata.json` with its `{process_id}.csv` in `data/inputdata/` (ELN downloads plus anything placed there manually).
3. **Validates and types** the metadata against `metadata-def.json`, producing an RDE-standard structured metadata record.
4. **Maps** the structured metadata onto ontology classes (Tensile Testing Process, Tensile Testpiece, Tensile Strength, Original Gauge Length, Identifier, Device Specification, etc.), producing a canonical JSON graph.

If the ELN can't be reached (no `.env`, network down), a warning is printed and the files already in `data/inputdata/` are still processed.

## Pipeline flow

```
eLabFTW (RDE = true)
        │  fetch_experiments()          (main.py, before rdetoolkit)
        ▼
data/inputdata/                         (rdetoolkit copies to data/raw/)
        {process_id}_metadata.json + {process_id}.csv
        │  get_input_files() / read_tensile_csv()
        ▼
Flat metadata dict + stress-strain DataFrame
        │  save_metadata()
        ▼
data/meta/{process_id}_metadata.json
        {"constant": {...}, "variable": []}
        │  transform_json_to_canonical()
        ▼
data/structured/{process_id}_canonical.json
        (ontology graph)
```

Alongside this, each run also writes a plain structured dump (`data/structured/{process_id}.json`), the measurement series (`data/structured/{process_id}.csv`), and validates `data/invoice/invoice.json` against `data/tasksupport/invoice.schema.json`.

## Repository layout

```
container/
├── main.py                              # ELN fetch, then rdetoolkit entry point
├── requirements.txt
├── modules/
│   ├── data_transformation.py           # parsing + the custom_dataset_function
│   ├── fetch_experiments_from_ELN.py    # eLabFTW API client
│   └── jsontocjson_tto.py               # metadata → ontology graph mapping
└── data/
    ├── inputdata/                       # ELN downloads + local metadata/CSV pairs
    ├── invoice/invoice.json             # submission metadata (input)
    ├── tasksupport/
    │   ├── metadata-def.json            # per-field schema: type, unit, ontology class
    │   ├── invoice.schema.json
    │   └── rdeconfig.yml
    ├── raw/                             # output: ELN downloads + copied inputs
    ├── meta/                            # output: typed structured metadata (per specimen)
    └── structured/                      # output: plain dump, CSV, and canonical ontology JSON
```

## Setup

Requires Python 3.12 and a virtual environment (`.rde-tto/`, kept out of git).

```bash
python3 -m venv .rde-tto
source .rde-tto/bin/activate
pip install -r container/requirements.txt
```

ELN access is configured via a `.env` file in the repository root (kept out of git):

```
ELAB_SERVER=https://<your-elabftw-host>
ELAB_KEY=<api key>
```

## Running it

rdetoolkit resolves all its paths relative to the **current working directory**, so run it from inside `container/`:

```bash
cd container
python main.py
```

Output lands in `container/data/meta/` and `container/data/structured/`, named per specimen (`{process_id}_metadata.json`, `{process_id}_canonical.json`, etc.).

`fetch_experiments_from_ELN.py` can also be run on its own to just download the experiments into `container/data/inputdata/`.
