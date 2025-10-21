
#%%
import sys
import glob
import numpy as np
import os
import pandas as pd
import pickle
from datetime import datetime
import logging
import importlib
import joblib
import re

import json

import mne

#from mne.preprocessing import (
 #   ICA, create_eog_epochs, create_ecg_epochs, corrmap)
from mne_icalabel import label_components #optional - only for preprocessing
from mne.utils import logger
from mne.channels import make_standard_montage
import mne_features
from collections import defaultdict

from mne.export import export_raw

from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

root_dir = os.path.abspath('/Users/michelle.george/Desktop/Speech2Song/Recordings/') # enter your own path to Recordings here!


#%% convert to EDF 

#%% # Define the directory containing the EEG files and the output directory -- FOR EDF files

eeg_dir = os.path.join(root_dir, 'Raw/Real_Data')

# Define the subject directories
'''List of subject directories to process -- This is structured such that every subject is a folder (sub-01 as example) and inside the folder the EDF file exists. Same with the raw files'''
sub_names = [d for d in os.listdir(eeg_dir) if os.path.isdir(os.path.join(eeg_dir, d))]
sub_names= sorted(sub_names, key=lambda x: (x.split('-')[1]))

#sub = 'sub-19'  #enter subject specific ID here!
#load raw EEG file
#%%
for sub in sub_names:
    s = re.search(r'\d+', sub).group() 
    sub_path = os.path.join(eeg_dir, sub)
    raw = None
    # eeg_file = os.path.join(sub_path, f'STS_Sleep{s}_session2-edf.edf')
    # if os.path.exists(eeg_file):
    #       try:
    #           raw = mne.io.read_raw_edf(eeg_file, preload=True)
    #           logging.info(f"Selected EDF file successfully loaded for {sub}")
             
    #       except Exception as e:
    #           logging.warning(f"Error loading session: {e}")

    #load the Raw files instead of the EDF files 

    eeg_file = os.path.join(sub_path,f'STS_Sleep{s}.eeg')
    vmrk_file = os.path.join(sub_path,f'STS_Sleep{s}.vmrk')
    vhdr_file = os.path.join(sub_path,f'STS_Sleep{s}.vhdr')
                
    if os.path.exists(eeg_file) and os.path.exists(vmrk_file) and os.path.exists(vhdr_file):
                    try:
                        # Read the EEG data using MNE
                        raw = mne.io.read_raw_brainvision(vhdr_file, preload=True)
                        
                        # Print the info for debugging
                        print(f"Loaded data for {sub}:")
                        print(raw.info)
                    except Exception as e:
                        print(f"Error loading BrainVision file for {sub}: {e}")   
    export_file = os.path.join(sub_path,f'STS_Sleep{s}-edf.edf')
              
    export_raw(export_file, raw, fmt="edf", physical_range=(-32768, 32767),overwrite=True)
    print(f"EDF file for {sub} exported successfully")   
    
    channel_types = {'HEOG': 'eog', 'VEOG': 'eog' 'EMG1': 'emg'}
    raw.set_channel_types(channel_types)

    # Check channel indices
    eog_indices = mne.pick_types(raw.info, meg=False, eog=True)
    logging.info(f"Number of EOG channels: {mne.pick_info(raw.info, eog_indices)['nchan']}")

    emg_indices = mne.pick_types(raw.info, meg=False, emg=True)
    logging.info(f"Number of EMG channels: {mne.pick_info(raw.info, emg_indices)['nchan']}")

    # Cleaned label (removes spacing inconsistencies)
    label_1 = 'Stimulus/S  1'
    label_9 = 'Stimulus/S  9'
    
    # Find all onsets of these labels
    onsets_1 = [onset for onset, desc in zip(raw.annotations.onset, raw.annotations.description)
                if desc.strip() == label_1.strip()]
    onsets_9 = [onset for onset, desc in zip(raw.annotations.onset, raw.annotations.description)
                if desc.strip() == label_9.strip()]
    
    # # Make sure there are at least two occurrences
    # if len(onsets_1) < 2 or len(onsets_9) < 2:
    #     raise ValueError("Less than 2 occurrences of one or both annotation labels.")
    
    # Get the second occurrences
    tmin = onsets_1[2]
    tmax = onsets_9[1]
    
    # Crop the raw data between those two onsets
    raw_cropped = raw.copy().crop(tmin=tmin, tmax=tmax)
    raw_cropped.notch_filter(freqs=[50, 100, 150, 200])
    raw_filt=None
    raw_filt = raw_cropped.filter(l_freq=0.1, h_freq=45, fir_design='firwin')
    
    #save the fif file 
    save_fif = os.path.join(sub_path, f'STS_Sleep{s}_Nap_filt.fif')
    raw_filt.save(save_fif, overwrite=True)
    
    #re-reference to mastoid in order to Score - EDF version for Scoring Hero
    raw_filt.resample(sfreq=100)
    ref_channels = ['TP9', 'TP10']
    
    mne.set_eeg_reference(raw_filt,ref_channels=ref_channels, projection=False,ch_type = 'eeg', copy= False)
    save_edf = os.path.join(sub_path, f'STS_Sleep{s}_Nap-edf.edf')
    export_raw(save_edf,raw_filt,fmt='edf', physical_range=(-32768, 32767),overwrite=True)
    print(f"EDF file for {sub} Nap session exported successfully")   

    del raw, raw_cropped
    
#%% Check USleep with Sleep scoring 

    #load USleep
    #staging path
for sub in sub_names:
    s = re.search(r'\d+', sub).group() 
    sub_path = os.path.join(eeg_dir, sub)
    score_path = os.path.join(sub_path, "scoring")
    usleep_path = os.path.join(score_path, f"STS_Sleep{s}_Nap-edf_hypnogram.npy")
    #load my score
    manual_path = os.path.join(score_path,f"STS_Sleep{s}_Nap-edf.json")
    # Check files
    if not os.path.exists(usleep_path):
        print(f"⚠️ Skipping {sub}: missing {usleep_path}")
        continue
    if not os.path.exists(manual_path):
        print(f"⚠️ Skipping {sub}: missing {manual_path}")
        continue
    
    print(f"✅ Processing {sub} ...")
    
    #load the files
    usleep_score = np.load(usleep_path)
    
    with open(manual_path) as f:
        manual = json.load(f)
    
    # Mapping dictionary
    stage_map = {
        "Wake": 0,
        "N1": 1,
        "N2": 2,
        "N3": 3,
        "REM": 4,

    }
    
    manual = manual[0]
    stages = [d["stage"] for d in manual]
    # Convert "Inconclusive" to "REM" before mapping
    stages = ["REM" if s == "Inconclusive" else s for s in stages]
    # Convert to numeric
    stage_nums = [stage_map.get(s, -1) for s in stages]

    stages_combined = np.column_stack((stages, stage_nums, usleep_score))

    # Compare columns 1 and 2 (index 1 and 2, since Python is 0-based)
    col2 = stages_combined[:,1].astype(int)
    col3 = stages_combined[:,2].astype(int)
    stages_combined = pd.DataFrame(stages_combined, columns=["Manual2_Labelled", "Manual2_Score", "Usleep"])

    matches = np.sum(col2 == col3)
    percentage = (matches / len(stages_combined)) * 100

    print(f"Matches: {matches}/{len(stages_combined)} = {percentage:.2f}%")
    mismatch_mask = col2 != col3
    mismatch_epochs = np.where(mismatch_mask)[0]  # epoch indices

    # Create a dataframe of mismatches for inspection
    mismatches_df = stages_combined.iloc[mismatch_epochs].copy()
    mismatches_df["Epoch"] = mismatch_epochs  # add epoch numbers

    #creating a confusion matrix to see the discrepancies
    cm = confusion_matrix(col2, col3, labels=list(stage_map.values()))
    
    #create label legends
    label_order = [k for k in stage_map.keys() if k!="None"]  # ["Wake", "N1", "N2", "N3", "REM", "None"]
    
    # Plot confusion matrix
    plt.figure(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=label_order,
                yticklabels=label_order)
    
    plt.xlabel("Usleep Prediction")
    plt.ylabel("Manual Scoring")
    plt.title("Confusion Matrix: Manual vs Usleep")
    #save the confusion plot
    plt_path = os.path.join("/Users/michelle.george/Desktop/Speech2Song/Plots/confusion_matrix/", f"{sub}_usleep_manual.png")
    plt.savefig(plt_path,dpi=300, bbox_inches="tight")
    plt.close()
    
#%% Check stimulation annotations with sleep scoring
for sub in sub_names:
    s = re.search(r'\d+', sub).group() 
    sub_path = os.path.join(eeg_dir, sub)
    raw = None
    eeg_file = os.path.join(sub_path, f'STS_Sleep{s}_Nap_filt.fif')  #only .fif for Nap has the annotations. The EDF does not. 
    if os.path.exists(eeg_file):
          try:
              raw = mne.io.read_raw_fif(eeg_file, preload=True)
              logging.info(f"Selected .fif NAP file successfully loaded for {sub}")
             
          except Exception as e:
              logging.warning(f"Error loading session: {e}")
    if raw is None:
        print(f"⚠️ Skipping {sub}: no raw FIF file")
        continue
    
    #load the Raw files instead of the EDF files 
    sub_path = os.path.join(eeg_dir, sub)
    score_path = os.path.join(sub_path, "scoring")
    usleep_path = os.path.join(score_path, f"STS_Sleep{s}_Nap-edf_hypnogram.npy")
    #load my score
    manual_path = os.path.join(score_path,f"STS_Sleep{s}_Nap-edf.json")
    # Check files
    if not os.path.exists(usleep_path):
        print(f"⚠️ Skipping {sub}: missing {usleep_path}")
        continue
    if not os.path.exists(manual_path):
        print(f"⚠️ Skipping {sub}: missing {manual_path}")
        continue
    
    print(f"✅ Processing {sub} ...")
    
    #load the files
    usleep_score = np.load(usleep_path)
    
    with open(manual_path) as f:
        manual = json.load(f)
        # Check files
    #load sleep scoring labels 
    
    # Mapping dictionary
    stage_map = {
        "Wake": 0,
        "N1": 1,
        "N2": 2,
        "N3": 3,
        "REM": 4,

    }
    
    manual = manual[0]
    stages = [d["stage"] for d in manual]
    # Convert "Inconclusive" to "REM" before mapping
    stages = ["REM" if s == "Inconclusive" else s for s in stages]
    # Convert to numeric
    stage_nums = [stage_map.get(s, -1) for s in stages]

    stages_combined = np.column_stack((stages, stage_nums, usleep_score))
    stages_combined = pd.DataFrame(stages_combined, columns=["Manual2_Labelled", "Manual2_Score", "Usleep"])


    #specify annotation parameters
    # Anchor = first existing annotation onset
    anchor = raw.annotations.onset[0]

    window = float(30)
    orig_time = raw.annotations.orig_time
    score_onset = [anchor + i * window for i in range(len(stages))] #mention either manual or the Usleep score here
    sl_annotations = mne.Annotations(onset=score_onset, duration=window, description=stages,orig_time=raw.annotations.orig_time)
    new_annotations = raw.annotations + sl_annotations
    raw.set_annotations(new_annotations)
    
    #check for mismatches
    sleep_stages = [(onset, onset + dur, desc) 
                for onset, dur, desc in zip(sl_annotations.onset,
                                           sl_annotations.duration,
                                           sl_annotations.description)]
    # Get stimulus annotations
    stimuli = [(onset, desc) 
               for onset, desc in zip(raw.annotations.onset,
                                      raw.annotations.description)
               if desc in ["Stimulus/S 1", "Stimulus/S 14"]]
    
    mismatches = []
    # Loop over epochs
    for idx, (start, end, stage) in enumerate(sleep_stages):
        # Find stimuli inside this 30s window
        stim_in_epoch = [stim for stim in stimuli if start <= stim[0] < end]
    
        for stim_onset, stim_desc in stim_in_epoch:
            # Rule check
            if stim_desc == "Stimulus/S 1" and stage != "Wake":
                mismatches.append([idx, stage, stim_desc])
            elif stim_desc == "Stimulus/S 14" and stage not in ["N2", "N3"]:
                mismatches.append([idx, stage, stim_desc])


    mpath = os.path.join("/Users/michelle.george/Desktop/Speech2Song/Data_Check/stimulation_mismatch/",f"{sub}_mismatches.npy")
    np.save(mpath, mismatches)
    print(f"💾 Saved mismatches for {sub} → {mpath}")