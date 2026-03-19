# EEG_preproc/scripts/run_preproc_batch.py

import sys
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from EEG_preproc.src.paths import load_paths_config
from EEG_preproc.src.pipeline_main import run_preproc_subject


if __name__ == "__main__":

    local_cfg = PROJECT_ROOT / "EEG_preproc/config/paths_local_michelle.yml"
    preproc_cfg_path = PROJECT_ROOT / "EEG_preproc/config/preproc_legacy.yml"

    paths = load_paths_config(local_cfg)

    with open(preproc_cfg_path) as f:
        preproc_cfg = yaml.safe_load(f)

    # -------- detect subjects from BIDS --------
    bids_root = Path(paths["bids_root"])

    SUBJECTS = sorted([
        p.name.replace("sub-", "")
        for p in bids_root.glob("sub-*")
        if p.is_dir()
    ])

    print("Subjects detected:", SUBJECTS)

    # -------- run pipeline --------
    for sub in SUBJECTS:

        print(f"\n=== Subject {sub} ===")

        try:
            run_preproc_subject(sub, paths, preproc_cfg)

        except Exception as e:
            print(f"Pipeline failed for sub-{sub}: {e}")