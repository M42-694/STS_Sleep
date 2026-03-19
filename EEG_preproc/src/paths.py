# EEG_preproc/src/paths.py
from pathlib import Path
import yaml

def load_paths_config(cfg_path: Path) -> dict:
    """Load local YAML config and create required directory structure."""
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    data_root   = Path(cfg["data_root"])
    bids_root   = Path(cfg["bids_root"].format(data_root=data_root))
    deriv_root  = Path(cfg["deriv_root"].format(data_root=data_root))
    logs_root   = Path(cfg["logs_root"].format(deriv_root=deriv_root))
    report_root = Path(cfg["report_root"].format(deriv_root=deriv_root))
    errors_root = Path(cfg["errors_root"].format(deriv_root=deriv_root))
    sleep_annotations_root = Path(cfg["sleep_annotations_root"].format(data_root=data_root))

    for p in [deriv_root, logs_root, report_root, errors_root]:
        p.mkdir(parents=True, exist_ok=True)

    return dict(
        project_name=cfg.get("project_name", "STS_Nap"),
        data_root=data_root,
        bids_root=bids_root,
        deriv_root=deriv_root,
        logs_root=logs_root,
        report_root=report_root,
        errors_root=errors_root,
        sleep_annotations_root=sleep_annotations_root,
    )