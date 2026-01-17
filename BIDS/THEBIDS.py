#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 
BIDS script for EEG data according to version 1.10.1, approved by BIDS Validator 
STS Nap Study

Input files: ".eeg", ".vhdr", ".vmdrk"

Output directory structure: bids_dataset/
├── dataset_description.json
├── participants.json
├── participants.tsv
├── README
└── sub-**/
    └── ses-01/
        ├── sub-**_ses-01_scans.tsv
        └── eeg/
            ├── sub-**_ses-01_task-sleep_channels.tsv
            ├── sub-**_ses-01_task-sleep_coordsystem.json
            ├── sub-**_ses-01_task-sleep_eeg.eeg
            ├── sub-**_ses-01_task-sleep_eeg.json
            ├── sub-**_ses-01_task-sleep_eeg.vhdr
            ├── sub-**_ses-01_task-sleep_eeg.vmrk
            ├── sub-**_ses-01_task-sleep_electrodes.tsv
            ├── sub-**_ses-01_task-sleep_events.json
            └── sub-**_ses-01_task-sleep_events.tsv
            
+ Manual modification of participants.tsv based on RedCap data
+ Manual addition of stimuli folder
+ Manual addition of behavioural tsvs

Last adapted on Jan 17 2025 
  Last updates on outlier events.tsv files:
        sub-07: ensure blocks only advance once stimuli are actually played ✅
        sub-12: ensure ses-02 continues where ses-01 left off ✅
        subs-13, -32, -41, -43, -45: ensure restart of musical wake 1 / musical nap does not advance blocks  ✅
        subs-21, -31, -33: ensure advancement of blocks despite lack of 'end of block' trigger ✅
        sub-44: ensure translation of wrong trigger labels and advancement of blocks despite lack of 'end of block' trigger ✅

@author(s): clara & ChatGPT-5
"""

import os
import json
import mne
import pandas as pd
import numpy as np
import re
from mne_bids import BIDSPath, write_raw_bids
from pathlib import Path

# --- Paths ---
data_dir = Path(os.path.expanduser("~/Downloads"))
bids_root = data_dir / "bids_dataset"
bids_root.mkdir(parents=True, exist_ok=True)

# --- Loop over all participants (vhdr files) ---
for fname in os.listdir(data_dir):
    if not fname.endswith(".vhdr"):
        continue
    vhdr_file = os.path.join(data_dir, fname)

    # --- Extract participant number and set as sub-** (two-digit) ---
    base = os.path.splitext(fname)[0]  # remove extension
    match = re.search(r'Sleep(\d+)', base)
    if match:
        sub_id = f"{int(match.group(1)):02d}"
    else:
        raise ValueError(f"Cannot extract participant number from {fname}")
        
    # --- Detect session from filename (default: ses-01) ---
    session = "01"
    if re.search(r'session\s*2|session_?2', base, re.IGNORECASE):
        session = "02"

    # --- Load EEG data ---
    raw = mne.io.read_raw_brainvision(vhdr_file, preload=False)

    # --- Remove unused channels (EOG_L, EOG_R, HEOG, WAV) ---
    unused_channels = {"EOG_L", "EOG_R", "HEOG", "WAV"}
    raw.pick([ch for ch in raw.ch_names if ch.upper() not in unused_channels])
    
    # --- Set channel types for EMG and remaining EOG (if present) ---
    ch_types = {}
    for ch in raw.ch_names:
        if ch.upper() in {"VEOG", "IO"}:
            ch_types[ch] = "eog"
        elif ch.upper() == "EMG":
            ch_types[ch] = "emg"
    raw.set_channel_types(ch_types)
    raw.set_montage('standard_1020', on_missing='ignore')

    # --- Ensure all digitized points use head coordinates ---
    if raw.info.get('dig'):
        for point in raw.info['dig']:
            point['coord_frame'] = mne.io.constants.FIFF.FIFFV_COORD_HEAD

    # --- Extract events ---
    trial_type_map = {
        'Stimulus/S  1': "stimulus: wake list",
        'Stimulus/S 14': "stimulus: nap list",
        'Stimulus/S  9': "end of block",
        'Stimulus/S  2': "instruction",
        'Stimulus/S  7': "response",
        'Stimulus/S  5': "stimulus: song",
        'Stimulus/S  6': "stimulus: speech"
    }
    onsets = raw.annotations.onset
    durations = raw.annotations.duration
    
    # --- SPECIAL CASE: Subject 44 trigger mapping translations (roughly) ---
    if sub_id == "44":
        trial_type_map_44 = {
            'Stimulus/S 13': "stimulus: song",
            'Stimulus/S 14': "stimulus: speech",
            'Stimulus/S  9': "stimulus: wake list",      
            'Stimulus/S  1': "stimulus: wake list",      
            'Stimulus/S 10': "instruction",
            'Stimulus/S 15': "response",
            'Response/R  5': "stimulus: nap list",       
            'Stimulus/S  8': "unkown",
            'Stimulus/S  7': "unknown",
            'Stimulus/S  5': "unknown",
            'Stimulus/S  3': "unknown",
            'Stimulus/S  2': "unknwon"
        }
        trial_types = [trial_type_map_44.get(desc, 'unknown') for desc in raw.annotations.description]
    else:
        trial_types = [trial_type_map.get(desc, 'unknown') for desc in raw.annotations.description]

    events_df = pd.DataFrame({'onset': onsets, 'duration': durations, 'trial_type': trial_types})

    trial_types_list = events_df["trial_type"].tolist()
    n_events = len(trial_types_list)
    blocks = []
    block_labels = ["musical wake 1", "musical nap", "musical wake 2", "passive listening"]
    
    # --- SPECIAL CASE 12 (2 SESSIONS): initial block depends on session ---
    if sub_id == "12" and session == "02":
        block_index = block_labels.index("musical nap")
    else:
        block_index = block_labels.index("musical wake 1")
    
    # --- Block advancement rules ---
    current_block = block_labels[block_index]
    stimulus_seen_in_block = False

    stimulus_trial_types = {"stimulus: wake list", "stimulus: nap list", "stimulus: song", "stimulus: speech"}
    
    i = 0
    while i < n_events:
        tt = trial_types_list[i]
        blocks.append(current_block)
    
        # mark stimulus seen
        if tt in stimulus_trial_types:
            stimulus_seen_in_block = True
    
        # handle end of block
        if tt == "end of block" and stimulus_seen_in_block:
            # look ahead until next end of block or end of events
            j = i + 1
            look_ahead_trial_types = []
            while j < n_events and trial_types_list[j] != "end of block":
                look_ahead_trial_types.append(trial_types_list[j])
                j += 1
    
            # apply special rules: musical nap cannot contain responses
            if current_block == "musical wake 1":
                if "response" not in look_ahead_trial_types:
                    block_index = min(block_index + 1, len(block_labels) - 1)
                    current_block = block_labels[block_index]
                    stimulus_seen_in_block = False
            elif current_block == "musical nap":
                if "response" in look_ahead_trial_types:
                    block_index = min(block_index + 1, len(block_labels) - 1)
                    current_block = block_labels[block_index]
                    stimulus_seen_in_block = False
            else:
                block_index = min(block_index + 1, len(block_labels) - 1)
                current_block = block_labels[block_index]
                stimulus_seen_in_block = False
    
        i += 1
    
    events_df.insert(2, "block", blocks)

    # --- SPECIAL CASE: Subject 21 manual block overrides ---
    if sub_id == "21":
        onset_block_map = [
            (2921.524, "musical nap"),
            (5185.474, "musical wake 2"),
            (5422.976, "passive listening")
        ]
        for onset_threshold, new_block in onset_block_map:
            events_df.loc[events_df['onset'] >= onset_threshold, 'block'] = new_block

    # --- SPECIAL CASE: Subject 31 manual block overrides ---
    if sub_id == "31":
        onset_block_map = [
            (1520.906, "musical nap"),
            (3581.142, "musical wake 2"),
            (5189.352, "passive listening")
        ]
        for onset_threshold, new_block in onset_block_map:
            events_df.loc[events_df['onset'] >= onset_threshold, 'block'] = new_block
            
    # --- SPECIAL CASE: Subject 33 manual block overrides ---
    if sub_id == "33":
        onset_block_map = [
            (1273.216, "musical nap"),
            (3555.064, "musical wake 2"),
            (4478.728, "passive listening")
        ]
        for onset_threshold, new_block in onset_block_map:
            events_df.loc[events_df['onset'] >= onset_threshold, 'block'] = new_block
            
    # --- SPECIAL CASE: Subject 44 manual block overrides ---
    if sub_id == "44":
         onset_block_map = [
             (1033.182, "musical nap"),
             (3408.556, "musical wake 2"),
             (4378.706, "passive listening")
         ]
         for onset_threshold, new_block in onset_block_map:
             events_df.loc[events_df['onset'] >= onset_threshold, 'block'] = new_block

    # --- Define BIDS path ---
    bids_path = BIDSPath(
        subject=sub_id,
        session=session,
        task="sleep",
        datatype="eeg",
        root=bids_root,
        suffix="eeg"
    )
    raw.info['subject_info'] = {'id': int(sub_id), 'sex': 1}
    write_raw_bids(raw, bids_path, overwrite=True)

    # --- SPECIAL CASE 12 (2 SESSIONS): remove unwanted CapTrak files for ses-02 ---
    if sub_id == "12" and session == "02":
        eeg_dir = bids_root / f"sub-{sub_id}" / f"ses-{session}" / "eeg"
    
        for fname in [
            f"sub-{sub_id}_ses-{session}_space-CapTrak_coordsystem.json",
            f"sub-{sub_id}_ses-{session}_space-CapTrak_electrodes.tsv",
        ]:
            fpath = eeg_dir / fname
            if fpath.exists():
                fpath.unlink()

    # --- SPECIAL CASE 12 (2 SESSIONS): reuse geometry files from ses-01 ---
    if sub_id == "12" and session == "02":
    
        eeg_dir_ses01 = bids_root / f"sub-{sub_id}" / "ses-01" / "eeg"
        eeg_dir_ses02 = bids_root / f"sub-{sub_id}" / "ses-02" / "eeg"
    
        for suffix in ["electrodes.tsv", "coordsystem.json"]:
            src = eeg_dir_ses01 / f"sub-{sub_id}_ses-01_task-sleep_{suffix}"
            dst = eeg_dir_ses02 / f"sub-{sub_id}_ses-02_task-sleep_{suffix}"
    
            if src.exists():
                dst.write_text(src.read_text())

    # --- Paths to BIDS files ---
    channels_tsv_path = bids_path.copy().update(suffix="channels", extension=".tsv").fpath
    electrodes_tsv_path = bids_path.copy().update(suffix="electrodes", extension=".tsv").fpath

    # --- Load channels.tsv and remove unused channels ---
    channels_df = pd.read_csv(channels_tsv_path, sep="\t")
    
    # Remove any rows corresponding to unwanted channels
    unused_channels = {"EOG_L", "EOG_R", "HEOG", "WAV"}
    channels_df = channels_df[~channels_df['name'].str.upper().isin(unused_channels)]
    
    # Set descriptions for remaining channels
    channels_df.loc[channels_df["type"] == "EEG", "description"] = "Electroencephalogram channel"
    channels_df.loc[channels_df["type"] == "EMG", "description"] = "Electromyogram (muscle)"
    channels_df.loc[channels_df["type"] == "EOG", "description"] = "Electrooculogram (eye)"
    
    # Save updated channels.tsv
    channels_df.to_csv(channels_tsv_path, sep="\t", index=False)
    print(f"Updated channels.tsv with filtered and corrected channels: {channels_tsv_path}")

    # --- Rename CapTrak files (to comply with naming logic) ---
    eeg_dir = os.path.join(bids_root, f"sub-{sub_id}", "ses-01", "eeg")
    if os.path.isdir(eeg_dir):
        for fname2 in os.listdir(eeg_dir):
            if "space-CapTrak" in fname2:
                new_fname = fname2.replace("space-CapTrak", "task-sleep")
                os.rename(os.path.join(eeg_dir, fname2), os.path.join(eeg_dir, new_fname))
                print(f"Renamed {fname2} → {new_fname}")

    # --- Create events.tsv ---
    events_tsv_path = bids_path.copy().update(suffix='events', extension='.tsv').fpath
    events_tsv_path.parent.mkdir(parents=True, exist_ok=True)
    events_df.to_csv(events_tsv_path, sep='\t', index=False, float_format='%.3f')

    # --- Create events.json ---
    events_json = {
        "onset": {"Description": "Time of the event onset from start of data", "Units": "seconds"},
        "duration": {"Description": "Duration of the event", "Units": "seconds"},
        "block": {
            "Description": "Block label for the event",
            "Levels": {
                "musical wake 1": "Hearing and rating speech and song excerpts while awake before napping",
                "musical nap": "Hearing speech and song excerpts while falling asleep and asleep",
                "musical wake 2": "Hearing and rating speech and song excerpts while awake after napping",
                "passive listening": "Hearing full songs or speeches"
            }
        },
        "trial_type": {
            "Description": "Type of the event/trial/trigger",
            "Levels": {
                "stimulus: wake list": "Hearing loops of speech and song stimuli belonging to the wake set",
                "stimulus: nap list": "Hearing loops of speech and song stimuli belonging to the nap set",
                "end of block": "The current block ended",
                "instruction": "Instructions are displayed on the task screen",
                "response": "Responses are given to instructions on the screen",
                "stimulus: song": "A song (excerpt) is played",
                "stimulus: speech": "A speech (excerpt) is played",
                "unknown": "Irrelevant input trigger"
            }
        }
    }
    with open(bids_path.copy().update(suffix='events', extension='.json').fpath, 'w') as f:
        json.dump(events_json, f, indent=4)

    # --- Create eeg.json ---
    eeg_json = {
        "TaskName": "sleep",
        "InstitutionName": "Paris Brain Institute (Institut du Cerveau)",
        "InstitutionAddress": "Hopital Pitie, 47 Boulevard de l'Hopital, 75013 Paris, France",
        "InstitutionalDepartmentName": "DreamTeam",
        "Manufacturer": "Brain Products",
        "ManufacturersModelName": "BrainAmp",
        "CapManufacturer": "EasyCap",
        "CapManufacturersModelName": "64Ch Standard BrainCap for BrainAmp, GACS-64, C-Cut",
        "EEGReference": "Cz",
        "EEGGround": "n/a",
        "PowerLineFrequency": "n/a",
        "EEGChannelCount": len(mne.pick_types(raw.info, eeg=True)),
        "MiscChannelCount": len(mne.pick_types(raw.info, misc=True)),
        "RecordingType": "continuous",
        "RecordingDuration": float(raw.times[-1]),
        "SamplingFrequency": raw.info['sfreq'],
        "EOGChannelCount": len(mne.pick_types(raw.info, eog=True)),
        "ECGChannelCount": len(mne.pick_types(raw.info, ecg=True)),
        "EMGChannelCount": len(mne.pick_types(raw.info, emg=True)),
        "SoftwareFilters": "n/a",
        "EEGPlacementScheme": "10 percent system"
    }
    eeg_json["HED"] = ""  # otherwise the validator complains about the HED
    with open(bids_path.copy().update(suffix='eeg', extension='.json').fpath, 'w') as f:
        json.dump(eeg_json, f, indent=4)

    # --- Create electrodes.tsv ---
    if os.path.exists(electrodes_tsv_path):
        electrodes_df = pd.read_csv(electrodes_tsv_path, sep='\t')
        # ensure x, y, z coordinate entries are numeric
        for coord in ['x', 'y', 'z']:
            if coord in electrodes_df.columns:
                electrodes_df[coord] = pd.to_numeric(electrodes_df[coord], errors='coerce')
        # add type of electrodes as column
        if 'type' not in electrodes_df.columns:
            electrodes_df.insert(electrodes_df.columns.get_loc('z') + 1, 'type', electrodes_df['name'].apply(lambda x: 'cup' if 'EMG' in x.upper() else 'ring'))
        # Remove unwanted channels from electrodes.tsv
        unused_channels = {"EOG_L", "EOG_R", "HEOG", "WAV"}
        electrodes_df = electrodes_df[~electrodes_df['name'].str.upper().isin(unused_channels)]

    else:
        montage = raw.get_montage()
        if montage and montage.get_positions():
            positions = montage.get_positions()['ch_pos']
            electrodes_df = pd.DataFrame({
                'name': list(positions.keys()),
                'x': [pos[0] for pos in positions.values()],
                'y': [pos[1] for pos in positions.values()],
                'z': [pos[2] for pos in positions.values()]
            })
        else:
            electrodes_df = pd.DataFrame({
                'name': raw.ch_names,
                'x': [np.nan]*len(raw.ch_names),
                'y': [np.nan]*len(raw.ch_names),
                'z': [np.nan]*len(raw.ch_names)
            })
        electrodes_df.insert(electrodes_df.columns.get_loc('z') + 1, 'type', electrodes_df['name'].apply(lambda x: 'cup' if 'EMG' in x.upper() else 'ring'))
    electrodes_df.to_csv(electrodes_tsv_path, sep='\t', index=False, na_rep='n/a')  # to ensure that missing values are represented by NaN values
    print(f"Final electrodes.tsv with 'type' column saved: {electrodes_tsv_path}")

    # --- Create coordsystem.json ---
    coordsystem_json_path = bids_path.copy().update(suffix='coordsystem', extension='.json').fpath
    coordsystem_json = {
        "EEGCoordinateSystem": "Other",
        "EEGCoordinateUnits": "m",
        "EEGCoordinateSystemDescription": (
            "RAS orientation: the X-axis goes from the left preauricular point through the right preauricular point. "
            "The Y-axis goes orthogonally to the X-axis through the nasion and inion. "
            "The Z-axis goes orthogonally to the XY-plane through the vertex of the head. "
            "Cz is located at 50% of the total distance between nasion and inion and at 50% of the total distance between the left and right preauricular points."
        )
    }
    with open(coordsystem_json_path, 'w') as f:
        json.dump(coordsystem_json, f, indent=4)
    print(f"coordsystem.json written to: {coordsystem_json_path}")

# --- Get all participant numbers from input files ---
input_files = [f for f in os.listdir(data_dir) if f.endswith('.vhdr')]
participant_numbers = []
for f in input_files:
    # Extract the number part after 'STS_Sleep'
    num_str = f.replace('STS_Sleep', '').split('.')[0]  
    try:
        participant_numbers.append(int(num_str))
    except ValueError:
        print(f"Warning: Could not parse participant number from {f}")
participant_numbers = sorted(participant_numbers)

# --- Create participants.tsv --- # gender, age, handedness, inclsuion needs to be filled in manually from RedCap
participant_ids = [f"sub-{num:02d}" for num in participant_numbers]
participants_df = pd.DataFrame({
    'participant_id': participant_ids,
    'gender': ['n/a'] * len(participant_ids),
    'age': ['n/a'] * len(participant_ids),
    'handedness': ['n/a'] * len(participant_ids),
    'inclusion': ['n/a'] * len(participant_ids)
})
participants_df.to_csv(os.path.join(bids_root, 'participants.tsv'), sep='\t', index=False)
print(f"participants.tsv written to: {os.path.join(bids_root, 'participants.tsv')}")

# --- Create participants.json ---
participants_json = {
    "participant_id": {"Description": "Unique participant identifier"},
    "gender": {"Description": "Gender of the participant", "Levels": {"M": "male", "F": "female", "O": "other"}},
    "age": {"Description": "Age of the participant", "Units": "years"},
    "handedness": {"Description": "Dominant hand of the participant", "Levels": {"right": "Right-handed", "left": "Left-handed", "ambidextrous": "Ambidextrous"}},
    "inclusion": {"Description": "Degree of inclusion in the different analyses", "Levels": {"full": "Included in all behavioural and EEG analyses", "partial: behaviour + nap": "Included in behavioural and nap EEG analyses", "partial: behaviour + wake": "Included in behavioural and wake EEG analyses"}}
}
with open(os.path.join(bids_root, 'participants.json'), 'w') as f:
    json.dump(participants_json, f, indent=4)

# --- Create dataset_description.json ---
dataset_description = {
    "Name": "STS Sleep Study",
    "BIDSVersion": "1.10.1",
    "DatasetType": "raw",
    "Authors": ["Michelle George", "Clara Hausen", "Giorgia Cantisani", "Aubrey Danjoux", "Daniel Presnitzer", "Thomas Andrillon"]
}
with open(os.path.join(bids_root, "dataset_description.json"), "w") as f:
    json.dump(dataset_description, f, indent=4)

# --- Create README ---
readme_text = """This dataset contains 42 subjects in total, of which 34 are included in all analyses, 40 only in behavioural and wake EEG analyses, 36 only in behavioural and nap EEG analyses. 
The experiment encompassed four consecutive blocks within one session. In blocks musical wake 1, musical nap, and musical wake 2 subjects listened to speech excerpts of which some elicited the speech-to-song (STS) illusion. The respective stimuli can be found in the speech2song sub-folder.
In the passive listening block, subjects listened to pairs of longer longer speeches and songs. The respective stimuli can be found in the passive listening sub-folder.
Exceptions: subject 12 (contains 2 sessions, one the continuation of the other), subject 44 (wrong triggers, partially translated).
- Clara Hausen (January 17, 2025) """
with open(os.path.join(bids_root, "README"), "w") as f:
    f.write(readme_text)

print(f"BIDS dataset created at: {bids_root}")
