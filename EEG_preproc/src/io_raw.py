# EEG_preproc/src/io_raw.py

from pathlib import Path
import pandas as pd
import mne


def load_raw_brainvision_bids(subject, session, bids_root):
    """
    Load BrainVision raw file and enforce channel structure from BIDS channels.tsv.

    Parameters
    ----------
    subject : str
        subject id without 'sub-' prefix
    session : str
        session id without 'ses-' prefix
    bids_root : Path
        root BIDS directory

    Returns
    -------
    raw : mne.io.Raw
    """

    eeg_dir = bids_root / f"sub-{subject}" / f"ses-{session}" / "eeg"

    vhdr_file = eeg_dir / f"sub-{subject}_ses-{session}_task-sleep_eeg.vhdr"
    channels_file = eeg_dir / f"sub-{subject}_ses-{session}_task-sleep_channels.tsv"
    electrodes_file = eeg_dir / f"sub-{subject}_ses-{session}_task-sleep_electrodes.tsv"

    print(f"Loading BrainVision file: {vhdr_file}")

    raw = mne.io.read_raw_brainvision(vhdr_file, preload=True)

    channels_df = pd.read_csv(channels_file, sep="\t")

    # keep only channels defined in BIDS
    bids_channels = channels_df["name"].tolist()

    raw.pick_channels(bids_channels)

    # map channel types
    type_map = {
        "EEG": "eeg",
        "EOG": "eog",
        "EMG": "emg",
        "MISC": "misc",
    }

    ch_types = {}

    for _, row in channels_df.iterrows():

        name = row["name"]
        ch_type = row["type"]

        if ch_type in type_map:
            ch_types[name] = type_map[ch_type]

    raw.set_channel_types(ch_types)
    # set montage (optional, but good to have correct channel locations for later processing steps, e.g. ICA topographies)
    raw = set_montage_from_bids(raw, electrodes_file)

    print(f"Channels loaded: {len(raw.ch_names)}")

    return raw

def set_montage_from_bids(raw, electrodes_file):
    """
    Attach electrode positions from BIDS electrodes.tsv to raw.
    """

    if electrodes_file is None or not electrodes_file.exists():
        print("No electrodes.tsv found — skipping montage")
        return raw

    electrodes = pd.read_csv(electrodes_file, sep="\t")

    pos = {}
    for _, row in electrodes.iterrows():
        pos[row["name"]] = [row["x"], row["y"], row["z"]]

    montage = mne.channels.make_dig_montage(
        ch_pos=pos,
        coord_frame="head"
    )

    raw.set_montage(montage, on_missing="ignore")

    print("Montage attached from electrodes.tsv")

    return raw


