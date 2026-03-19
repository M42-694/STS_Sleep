# EEG_preproc/src/session_segmentation.py

from pathlib import Path
import pandas as pd
import numpy as np
import mne

from EEG_preproc.src import paths

def crop_raw_with_safe_annotations(raw, start, end):
    """
    Crop raw safely and rebase annotations to avoid MNE cropping issues.
    """

    orig_ann = raw.annotations

    in_win = (orig_ann.onset >= start) & (orig_ann.onset <= end)
    ann_subset = orig_ann[in_win]

    fixed_ann = mne.Annotations(
        onset=(ann_subset.onset - start).astype(float),
        duration=np.asarray(ann_subset.duration, dtype=float),
        description=ann_subset.description,
        orig_time=None
    )

    raw_crop = raw.copy().crop(tmin=start, tmax=end)

    # rebuild raw object to reset time axis
    data = raw_crop.get_data()
    info = raw_crop.info.copy()

    raw_new = mne.io.RawArray(data, info)

    old_ann = raw_crop.annotations

    rebased_ann = mne.Annotations(
        onset=old_ann.onset - raw_crop.first_time,
        duration=old_ann.duration,
        description=old_ann.description,
        orig_time=None
    )

    raw_new.set_annotations(rebased_ann + fixed_ann)

    return raw_new


def split_raw_by_bids_events(raw, events_tsv):
    """
    Segment raw recording into phases using BIDS events.tsv.
    """

    events = pd.read_csv(events_tsv, sep="\t")

    block_map = {
        "musical wake 1": "Wake1",
        "musical nap": "Nap",
        "musical wake 2": "Wake2",
        "passive listening": "Passive",
    }

    phases = {}

    for block_name, phase_name in block_map.items():

        rows = events[events["block"] == block_name]

        if rows.empty:
            print(f"WARNING: {block_name} not found")
            continue

        start = rows["onset"].min()
        end = (rows["onset"] + rows["duration"]).max()

        raw_phase = crop_raw_with_safe_annotations(raw, start, end)

        phases[phase_name] = raw_phase

        print(f"{phase_name}: {start:.2f}s → {end:.2f}s")

    return phases

def save_phase_raws(phases, subject, deriv_root, pipeline_name="preproc_legacy"):
    """
    Save segmented raw phases to derivatives.

    Parameters
    ----------
    phases : dict
        {phase_name: raw_object}
    subject : str
        subject id (without sub- prefix)
    deriv_root : Path
        root derivatives folder
    pipeline_name : str
        pipeline folder name
    phase_name : str
        "nap" or "wake1/2" or "passive" (for folder labelling and report sections)
    """



    for phase_name, raw_phase in phases.items():
        duration = raw_phase.times[-1]

        if duration < 60:
            print(f"WARNING: {phase_name} very short ({duration:.1f}s)")

        phase_label = phase_name.lower()

        #define the path to save the raw file for this phase
        out_dir = Path(deriv_root)/ pipeline_name / phase_name.lower() / f"sub-{subject}"
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = out_dir / f"sub-{subject}_task-{phase_label}_raw.fif"

        raw_phase.save(fname, overwrite=True)

        print(f"[Saved] {fname}")


def extract_nap_stimulus_times(events_tsv, nap_start, nap_end):

    events = pd.read_csv(events_tsv, sep="\t")

    nap_rows = events[events["block"] == "musical nap"]

    stim_onsets = nap_rows["onset"].values

    stim_times = stim_onsets - nap_start

    stim_times = stim_times[(stim_times >= 0) & (stim_times <= (nap_end-nap_start))]

    return stim_times