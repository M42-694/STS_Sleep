# EEG_preproc/scripts/run_preproc_subject.py
'''improvements: Can add argparse for subject ID to include sub_ID directly while running script from Terminal'''

import sys
from pathlib import Path
import yaml 
import argparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from EEG_preproc.src.paths import load_paths_config
from EEG_preproc.src.pipeline_main import run_preproc_subject


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--sub", required=True)

    args = parser.parse_args()

    subject_id = args.sub

    print(f"\nRunning preprocessing for subject {subject_id}\n")

    local_cfg = PROJECT_ROOT / "EEG_preproc/config/paths_local_michelle.yml"
    preproc_cfg_path = PROJECT_ROOT / "EEG_preproc/config/preproc_legacy.yml"

    if not local_cfg.exists():
        raise FileNotFoundError(local_cfg)

    if not preproc_cfg_path.exists():
        raise FileNotFoundError(preproc_cfg_path)

    paths = load_paths_config(local_cfg)

    with open(preproc_cfg_path) as f:
        preproc_cfg = yaml.safe_load(f)

    run_preproc_subject(subject_id, paths, preproc_cfg)



