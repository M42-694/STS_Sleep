#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 16:55:30 2024

@author: michellegeorge
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample
import os
import pandas as pd

# Param
sampleRate = 44100  # Hz
N_REP = 8
pause = 0.5         # sec

# Triggers
T_trigger = 0.010    # sec
A_trigger = 0.99     # original: 0.8      
N = int(sampleRate*T_trigger)

# get current path
thisDir = os.getcwd()
folder_input = '/Users/michellegeorge/Desktop/SnS/Scripts/Nap_SnS/input/stimuli'
folder_output = '/Users/michellegeorge/Desktop/SnS/Scripts/Nap_SnS/input/'
#folder_output_concat = f'../../Datasets/DatasetSpeech2Song/stimuli_Praat/44.1kHz+triggers_concatenated_{N_REP}times/'
folder_output_here = './input_new/stimuli/'
folder_output_concat_here = f'./input_new/rep_concatenated_{N_REP}times/' 
types = ["song", "speech", "unlabelled"] 

file_list, sound_type = [], []
for stim_type in types:
    cur_file_list = os.listdir(os.path.join(thisDir, folder_input, stim_type))
    # Filter out hidden files like .DS_Store
    cur_file_list = [file for file in cur_file_list if not file.startswith(".")]
    file_list.extend(cur_file_list)
    sound_type.extend([stim_type] * len(cur_file_list))

sound_list = pd.DataFrame({'sound': file_list, 'type': sound_type})
n_stimulus = len(file_list)

# record sampling rate
sample_rate_list = []

energy_max = 0

for idx in range(n_stimulus):
    cur_wav_file = sound_list['sound'][idx]
    cur_wav_type = sound_list['type'][idx]
    cur_path = os.path.join(thisDir, folder_input, cur_wav_type, cur_wav_file)
    print('Processing audio file: ' + cur_wav_type + ', ' + cur_wav_file)

    # Load audio and get sampling rate
    cur_sample_rate, data = wavfile.read(cur_path)
    sample_rate_list.append(cur_sample_rate)

    # Ensure mono and 1D array
    if data.ndim == 2:  # Stereo file
        print(f"Stereo file detected: {cur_wav_file}. Converting to mono.")
        data = np.mean(data, axis=1)  # Average channels to make mono

    # Ensure it's 1D and cast to float if needed
    data = data.flatten().astype(np.float32)

    # Normalize energy: all have unitary energy
    data = data / float(np.std(data))

    # Update global maximum energy
    candidate_max = float(np.max(data))
    if candidate_max > energy_max:
        energy_max = candidate_max

# Save original sampling rate
sound_list['sample rate'] = sample_rate_list


# Normalize with global max
energy_max = float(energy_max)
for idx in range(n_stimulus):
    cur_wav_file = sound_list['sound'][idx]
    cur_wav_type = sound_list['type'][idx]
    cur_path = os.path.join(thisDir, folder_input, cur_wav_type, cur_wav_file)
    
    # Read audio file
    cur_sample_rate, data = wavfile.read(cur_path)
    print('Processing audio file: ' + cur_wav_type + ', ' + cur_wav_file)

    # Ensure data is mono
    if data.ndim == 2:  # Stereo
        print(f"Stereo file detected: {cur_wav_file}. Converting to mono.")
        data = np.mean(data, axis=1)  # Convert to mono

    # Resample if needed
    if cur_sample_rate != sampleRate:
        # Calculate the new number of sample points
        num_samples = int(len(data) * sampleRate / cur_sample_rate)
        # Resample
        data = resample(data, num_samples)
        cur_sample_rate = sampleRate
        print('Resampling done.')

    # Normalize energy: all have unitary energy
    data = data / float(np.std(data))

    # Normalize over global energy
    data *= 0.8 / energy_max

    # Create triggers
    trigger = np.zeros(len(data))
    trigger[:N] = A_trigger
    cur_sound_data = np.column_stack((data, trigger))

    # Save normalized audio
    save_folder = os.path.join(thisDir, folder_output, cur_wav_type)
    os.makedirs(save_folder, exist_ok=True)
    wavfile.write(os.path.join(save_folder, cur_wav_file), cur_sample_rate, cur_sound_data)

    save_folder = os.path.join(thisDir, folder_output_here, cur_wav_type)
    os.makedirs(save_folder, exist_ok=True)
    wavfile.write(os.path.join(save_folder, cur_wav_file), cur_sample_rate, cur_sound_data)

    # Create a version concatenated N_REP times with pause
    pause_data = np.zeros(int(pause * cur_sample_rate))  # Create pause as 1D
    data_with_pause = np.concatenate([data, pause_data])  # Add pause
    data_concat = np.tile(data_with_pause, N_REP)  # Repeat N_REP times
    trigger_concat = np.zeros(len(data_concat))
    trigger_concat[:N] = A_trigger  # Add trigger to the first N samples
    cur_sound_data_concat = np.column_stack((data_concat, trigger_concat))

    # Save concatenated audio
    save_folder = os.path.join(thisDir, folder_output_concat_here, cur_wav_type)
    os.makedirs(save_folder, exist_ok=True)
    wavfile.write(os.path.join(save_folder, cur_wav_file), cur_sample_rate, cur_sound_data_concat)

print('Done!')