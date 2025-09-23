import os
import numpy as np
import pandas as pd
from scipy.io import wavfile

# Parameters
sampleRate = 44100  # Hz
N_REP = 8
pause = 0.5  # seconds

# Triggers
T_trigger = 0.010  # seconds
A_trigger = 0.99  # Amplitude, original: 0.8
N = int(sampleRate * T_trigger)

# Paths
thisDir = os.getcwd()
#folder_input = '/Users/michelle.george/Desktop/Speech2Song/Scripts/Nap_SnS/input/Stimuli2/'
folder_input = '/Users/michelle.george/Desktop/Speech2Song/Scripts/speech2song_psychopy/input/stimuli'

folder_output = '/Users/michelle.george/Desktop/Speech2Song/Scripts/Nap_SnS/input/'


folder_output_concat_here = f'./input_new/rep_concatenated_{N_REP}times/' 

# File types to process
types = ["song", "speech"]

# Ensure output directory exists
os.makedirs(folder_output_here, exist_ok=True)
#os.makedirs(folder_output_concat_here, exist_ok=True)

# Get list of files and types
file_list, sound_type = [], []
for stim_type in types:
    cur_file_list = os.listdir(os.path.join(folder_input, stim_type))
    # Filter out hidden files like .DS_Store
    cur_file_list = [file for file in cur_file_list if not file.startswith(".")]
    file_list.extend(cur_file_list)
    sound_type.extend([stim_type] * len(cur_file_list))

sound_list = pd.DataFrame({'sound': file_list, 'type': sound_type})
n_stimulus = len(file_list)

# Initialize list to record sampling rates
sample_rate_list = []

# Process files
for idx in range(n_stimulus):
    cur_wav_file = sound_list['sound'][idx]
    cur_wav_type = sound_list['type'][idx]
    cur_path = os.path.join(folder_input, cur_wav_type, cur_wav_file)
    print(f'Processing audio file: {cur_wav_type}, {cur_wav_file}')

    # Load audio file and get sampling rate
    cur_sample_rate, data = wavfile.read(cur_path)
    sample_rate_list.append(cur_sample_rate)

    # Ensure the sample rate matches the specified rate
    if cur_sample_rate != sampleRate:
        raise ValueError(f"Sample rate mismatch in file {cur_wav_file}: expected {sampleRate}, got {cur_sample_rate}")

    # Create silence interval
    silence_samples = int(sampleRate * pause)
    silence = np.zeros(silence_samples, dtype=data.dtype)

    # Repeat the audio with silence intervals
    looped_with_silence = []
    for _ in range(N_REP):
        looped_with_silence.append(data)
        looped_with_silence.append(silence)

    # Combine into a single array
    looped_with_silence = np.concatenate(looped_with_silence)

    # Save the output file
    output_path = os.path.join(folder_output_concat_here, f"{cur_wav_type}_{cur_wav_file}_rep{N_REP}.wav")
    wavfile.write(output_path, sampleRate, looped_with_silence)

print(f"All processed files are saved in: {folder_output_concat_here}")
