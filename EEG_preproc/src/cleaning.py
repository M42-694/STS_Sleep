
import numpy as np
import mne
from pathlib import Path
import sys

# -------------------------------------------------------
# Add NICE-packages to Python path
# -------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

NICE_DIR = PROJECT_ROOT / "NICE-packages"

if str(NICE_DIR) not in sys.path:
    sys.path.insert(0, str(NICE_DIR))

# import NICE function
from nice_ext.algorithms.adaptive import _adaptive_egi

# -------------------------------------------------------
# Helper: run adaptive cleaning on a group of epochs
# -------------------------------------------------------

def _run_adaptive_group(epochs_group, params):

    # reject = {k: float(v) for k, v in params["reject"].items()}

    bad_channels, bad_epochs = _adaptive_egi(
        epochs_group,
        reject=float(params["reject"]),
        n_epochs_bad_ch=float(params["n_epochs_bad_ch"]),
        n_channels_bad_epoch=float(params["n_channels_bad_epoch"]),
        zscore_thresh=float(params["zscore_thresh"]),
        max_iter=int(params["max_iter"]),
        summary=None,
    )

    return bad_channels, bad_epochs


# -------------------------------------------------------
# Main NICE cleaning function
# -------------------------------------------------------

def run_nice_cleaning(
    raw,
    epochs,
    session_type,
    pipeline_cfg,
    subject_id
):
    """
    Run NICE artifact detection and apply results to raw data.

    Steps
    -----
    1 detect bad channels / bad epochs using _adaptive_egi
    2 combine across groups
    3 annotate BAD_EPOCH on raw
    4 interpolate raw bad channels
    5 average reference raw
    6 return QC metrics
    """

    combined_bad_chans = []
    combined_bad_epochs = []
    group_results = {}

    # session-level epoch count
    epochs_before_session = len(epochs)

    # ---------------------------------------------------
    # Determine group structure
    # ---------------------------------------------------
    cleaning_cfg = pipeline_cfg["cleaning"]

    if session_type.lower() == "nap":

        group_map = {
            "Group1": cleaning_cfg["group1"],
            "Group2": cleaning_cfg["group2"]
        }
        # params = {
        #     "group1": pipeline_cfg["cleaning"]["group1"],
        #     "group2": pipeline_cfg["cleaning"]["group2"]
        # }

    else:
        # wake phases only use group1 thresholds``
        group_map = {
            "Group1": cleaning_cfg["group1"]
        }
        # params = {
        #     "group1": pipeline_cfg["cleaning"]["group1"]
        # }

    # ---------------------------------------------------
    # Run adaptive cleaning per group
    # ---------------------------------------------------

    for group_name, params in group_map.items():

        if group_name not in epochs.event_id:
            continue

        epochs_group = epochs[group_name].copy()

        bad_chans, bad_epochs_local = _run_adaptive_group(
            epochs_group,
            params
        )

        # convert local epoch indices → global indices
        bad_epochs_global = [
            int(epochs_group.selection[i]) for i in bad_epochs_local
        ]

        combined_bad_chans.extend(bad_chans)
        combined_bad_epochs.extend(bad_epochs_global)

        epochs_before = len(epochs_group)
        bad_epoch_count = len(bad_epochs_global)
        epochs_after = epochs_before - bad_epoch_count

        group_results[group_name] = {
            "bad_channels": bad_chans,
            "bad_epochs": bad_epochs_global,
            "epochs_before": epochs_before,
            "epochs_after": epochs_after,
            "bad_channel_count": len(bad_chans),
            "bad_epoch_count": bad_epoch_count,
            "bad_channel_percent": (
                len(bad_chans) / epochs.info["nchan"] * 100
                if epochs.info["nchan"] > 0 else 0
            ),
            "bad_epoch_percent": (
                bad_epoch_count / epochs_before * 100
                if epochs_before > 0 else 0
            ),
        }

    # ---------------------------------------------------
    # Deduplicate results across groups
    # ---------------------------------------------------

    combined_bad_chans = sorted(set(combined_bad_chans))
    combined_bad_epochs = sorted(set(combined_bad_epochs))

    # ---------------------------------------------------
    # Mark bad channels on raw
    # ---------------------------------------------------

    raw.info["bads"] = list(set(raw.info["bads"] + combined_bad_chans))

    # ---------------------------------------------------
    # Annotate BAD_EPOCH on raw
    # ---------------------------------------------------

    if len(combined_bad_epochs) > 0:

        sfreq = raw.info["sfreq"]

        onset_samples = epochs.events[combined_bad_epochs, 0]
        onset_times = onset_samples / sfreq

        epoch_duration = epochs.tmax - epochs.tmin

        bad_annotations = mne.Annotations(
            onset=onset_times,
            duration=[epoch_duration] * len(onset_times),
            description=["BAD_EPOCH"] * len(onset_times),
        )

        if raw.annotations is None:
            raw.set_annotations(bad_annotations)
        else:
            raw.set_annotations(raw.annotations + bad_annotations)

    # ---------------------------------------------------
    # Interpolate EEG bad channels
    # ---------------------------------------------------

    eeg_bad_chans = [
        ch for ch in combined_bad_chans
        if raw.get_channel_types(picks=[ch])[0] == "eeg"
    ]

    if len(eeg_bad_chans) > 0:
        raw.interpolate_bads(reset_bads=True)

    # ---------------------------------------------------
    # Average reference
    # ---------------------------------------------------

    ref_cfg = cleaning_cfg["eeg_reference"]

    raw.set_eeg_reference(
        ref_cfg["type"],
        projection=ref_cfg["projection"]
    )

    # ---------------------------------------------------
    # QC metrics
    # ---------------------------------------------------

    qc_metrics = {

        "subject": subject_id,
        "session": session_type,

        "epochs_before": epochs_before_session,
        "bad_epoch_count": len(combined_bad_epochs),

        "bad_channel_count": len(combined_bad_chans),
        "bad_channels": combined_bad_chans,

        "bad_epochs": combined_bad_epochs,
        "epochs_after": epochs_before_session - len(combined_bad_epochs),

        "groups": group_results
    }

    return raw, qc_metrics


def save_preica_raws(
    phases,
    subject,
    deriv_root,
    pipeline_name="preproc_legacy"
):
    """
    Save phase raw files after NICE cleaning but before ICA.

    Parameters
    ----------
    phases : dict
        {phase_name: raw_object}
    subject : str
        subject id (without 'sub-' prefix)
    deriv_root : Path or str
        root derivatives folder
    pipeline_name : str
        pipeline folder name
    """

    for phase_name, raw_phase in phases.items():

        phase_label = phase_name.lower()

        duration = raw_phase.times[-1]

        if duration < 60:
            print(f"WARNING: {phase_label} very short ({duration:.1f}s)")

        out_dir = (
            Path(deriv_root)
            / pipeline_name
            / phase_label
            / f"sub-{subject}"
        )

        out_dir.mkdir(parents=True, exist_ok=True)

        fname = (
            out_dir
            / f"sub-{subject}_task-{phase_label}_desc-preICA_raw.fif"
        )

        raw_phase.save(fname, overwrite=True)

        print(f"[Saved preICA] {fname}")
