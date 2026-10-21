"""
Fetches tensile-test experiments from eLabFTW.

Every experiment whose title matches TARGET_TITLE and whose extra field
"RDE" is set to true is pulled down as:
  - {process_id}_metadata.json : the key/value data from the experiment's
                                 HTML tables (see extract_prefixed_table_data)
  - {process_id}.csv           : the attached measurement CSV
  - any other attachments, under their original names

Server URL and API key come from the ELAB_SERVER / ELAB_KEY environment
variables (loaded from .env when present).
"""
import os
import re
import json
from pathlib import Path
import requests
import urllib3
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
# The eLabFTW instance uses a self-signed certificate (verify=False below)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_TITLE = "Tensile-test-ontology"
REQUEST_TIMEOUT = 60


def _elab_config() -> tuple[str, dict]:
    elab_server_url = os.getenv("ELAB_SERVER")
    elab_token = os.getenv("ELAB_KEY")
    if not elab_server_url or not elab_token:
        raise RuntimeError("ELAB_SERVER and ELAB_KEY must be set (e.g. in .env)")
    return elab_server_url.rstrip("/"), {"Authorization": elab_token}


def extract_prefixed_table_data(html_body):
    """
    Parses HTML tables.
    If a table has a 'machine' column, it prefixes other keys with the machine name.
    """
    extracted_data = {}
    soup = BeautifulSoup(html_body, 'html.parser')
    tables = soup.find_all('table')

    for table in tables:
        rows = table.find_all('tr')
        if len(rows) < 2:
            continue

        # 1. Get headers and find if 'machine' exists
        headers = [td.get_text(strip=True).lower() for td in rows[0].find_all('td')]

        # Check if this is a 'Device' table
        has_machine_col = "machine" in headers
        machine_idx = headers.index("machine") if has_machine_col else -1

        # 2. Process data rows
        for data_row in rows[1:]:
            cells = [td.get_text(strip=True) for td in data_row.find_all('td')]

            # Skip rows that are shorter than headers
            if len(cells) < len(headers):
                continue

            # Determine prefix if 'machine' column exists
            prefix = ""
            if has_machine_col:
                machine_val = cells[machine_idx]
                if machine_val and machine_val != '\xa0':
                    # Create prefix: "Tensile Test Machine" -> "tensiletestmachine"
                    prefix = re.sub(r'[^a-zA-Z0-9]+', '', machine_val.lower())

            # 3. Zip headers and values together
            for i, (header, val) in enumerate(zip(headers, cells)):
                # Skip the machine column itself
                if has_machine_col and i == machine_idx:
                    continue

                # Only process non-empty values
                if val and val != '\xa0' and val.strip() != '':
                    # Clean the header (e.g. "Serial Number" -> "serial_number")
                    clean_header = re.sub(r'[^a-zA-Z0-9]+', '_', header).strip('_')

                    # Apply prefix if we found one
                    if prefix:
                        key = f"{prefix}_{clean_header}"
                    else:
                        key = clean_header

                    extracted_data[key] = val

    if not extracted_data.get("process_id"):
        if extracted_data.get("tensiletestpiece_id"):
            extracted_data["process_id"] = extracted_data["tensiletestpiece_id"]

    return extracted_data


def save_clean_json(exp_data, target_dir: str | Path) -> str:
    """
    Creates a JSON file containing ONLY the table data.
    Returns the process_id the file was saved under.
    """
    metadata = extract_prefixed_table_data(exp_data.get('body') or '')
    process_id = str(metadata.get("process_id", exp_data.get('id')))
    metadata.setdefault("process_id", process_id)
    file_path = Path(target_dir) / f"{process_id}_metadata.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    return process_id


def download_attachments(exp_id, process_id, target_dir: str | Path) -> list[Path]:
    """
    Fetches the list of files attached to the experiment and downloads them.
    The measurement CSV is renamed to {process_id}.csv.
    """
    elab_server_url, headers = _elab_config()
    saved = []

    # 1. Get the list of uploads for this experiment
    list_url = f"{elab_server_url}/api/v2/experiments/{exp_id}/uploads"
    response = requests.get(list_url, headers=headers, verify=False, timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        print(f"Failed to get uploads for experiment {exp_id}: HTTP {response.status_code}")
        return saved

    for up in response.json():
        file_id = up['id']
        original_name = up['real_name']
        if original_name.lower().endswith('.csv'):
            save_name = f"{process_id}.csv"
        else:
            save_name = original_name

        # 2. Download the actual file content
        dl_url = f"{elab_server_url}/api/v2/experiments/{exp_id}/uploads/{file_id}?format=binary"
        file_data = requests.get(dl_url, headers=headers, verify=False, timeout=REQUEST_TIMEOUT)

        if file_data.status_code == 200:
            file_save_path = Path(target_dir) / save_name
            with open(file_save_path, "wb") as f:
                f.write(file_data.content)
            saved.append(file_save_path)
            print(f"Saved file to: {file_save_path}")
        else:
            print(f"Failed to download {original_name} from experiment {exp_id}: HTTP {file_data.status_code}")

    return saved


def get_experiments_by_title(target_title: str) -> list:
    """
    Retrieves experiments from the eLabFTW server that match a specific title
    string and have the extra field "RDE" set to true.
    """
    elab_server_url, headers = _elab_config()
    url = f"{elab_server_url}/api/v2/experiments"

    query_params = {
        "q": f'"{target_title}"',
        "limit": 100
    }

    response = requests.get(url, headers=headers, params=query_params, verify=False, timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        raise RuntimeError(f"HTTP Status {response.status_code}: {response.text}")

    filtered_matches = []
    for exp in response.json():
        metadata_str = exp.get("metadata")
        if not metadata_str:
            continue
        try:
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError:
            continue
        rde_val = metadata.get("extra_fields", {}).get("RDE", {}).get("value")
        if rde_val is True or str(rde_val).lower() == "true":
            filtered_matches.append(exp)

    return filtered_matches


def fetch_experiments(target_dir: str | Path, target_title: str = TARGET_TITLE) -> list[Path]:
    """
    Downloads every RDE-flagged experiment (metadata JSON + attachments)
    into target_dir. Returns the paths of all files written.
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for exp in get_experiments_by_title(target_title):
        process_id = save_clean_json(exp, target_dir)
        written.append(target_dir / f"{process_id}_metadata.json")
        written.extend(download_attachments(exp['id'], process_id, target_dir))
    return written


if __name__ == "__main__":
    fetch_experiments(Path(__file__).resolve().parents[1] / "data" / "inputdata")
