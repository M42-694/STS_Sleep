import numpy as np
from scipy.io import wavfile
from scipy.signal import resample
import os
import pandas as pd

# Param
sampleRate = 44100  # Hz
N_REP = 20
pause = 0.5         # sec

# Triggers
T_trigger = 0.010    # sec
A_trigger = 0.99     # original: 0.8      
N = int(sampleRate*T_trigger)

# get current path
thisDir = os.getcwd()
#folder_input = '../../Datasets/DatasetSpeech2Song/stimuli_Praat/Originals/'
folder_input = './input/stimuli'
#folder_output = '../../Datasets/DatasetSpeech2Song/stimuli_Praat/44.1kHz+triggers/'
folder_output = './output/'
#folder_output_concat = f'../../Datasets/DatasetSpeech2Song/stimuli_Praat/44.1kHz+triggers_concatenated_{N_REP}times/'
folder_output_concat = './input/rep_concateneted_16times'
folder_output_here = './input/stimuli/'
folder_output_concat_here = f'./input/rep_concatenated_{N_REP}times/' 
types = ["song", "speech", "unlabelled"] 

file_list, sound_type = [], []
for type in types:
    cur_file_list = os.listdir(os.path.join(thisDir,folder_input, type))
    file_list = file_list + cur_file_list
    sound_type = sound_type + [type] * len(cur_file_list)
sound_list = pd.DataFrame({'sound': file_list, 'type': sound_type})
n_stimulus = len(file_list)

# record sampling rate
sample_rate_list = []

# Find global max
energy_max = 0
for idx in range(n_stimulus):
    cur_wav_file = sound_list['sound'][idx]
    cur_wav_type = sound_list['type'][idx]
    cur_path = os.path.join(thisDir, folder_input, cur_wav_type, cur_wav_file)
    print('Processing audio file: ' + cur_wav_type, ', ', cur_wav_file)

    # Load audio and get sampling rate
    cur_sample_rate, data = wavfile.read(cur_path)
    sample_rate_list.append(cur_sample_rate)

    # check mono or stereo
    if data.ndim != 1:
        raise ValueError("The file is not mono audio file.")
    
    # Normalize energy: al has unitary energy
    data = data/float(np.std(data))

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
    cur_path = os.path.join(thisDir,folder_input, cur_wav_type, cur_wav_file)
    
    # Read audio file
    cur_sample_rate, data = wavfile.read(cur_path)
    print('Processing audio file: ' + cur_wav_type, ', ', cur_wav_file)

    # resample if needed
    if cur_sample_rate != sampleRate:
        # calculate the new number of sample points
        num_samples = int(len(data) * sampleRate / cur_sample_rate)
        # resampling
        data = resample(data, num_samples)
        # update new sampling rate
        cur_sample_rate = sampleRate
        print('Resampling done.')

    # Normalize energy: al has unitary energy
    data = data/float(np.std(data))

    # Normalize over global energy
    data *= 0.8 / energy_max

    # Create triggers
    trigger = np.zeros(len(data))
    trigger[:N] = A_trigger
    cur_sound_data = np.column_stack((data, trigger))

    # Save new files
    save_folder = os.path.join(thisDir, folder_output, cur_wav_type)
    os.makedirs(save_folder, exist_ok=True)
    wavfile.write(os.path.join(save_folder, cur_wav_file), cur_sample_rate, cur_sound_data)
    save_folder = os.path.join(thisDir, folder_output_here, cur_wav_type)
    os.makedirs(save_folder, exist_ok=True)
    wavfile.write(os.path.join(save_folder, cur_wav_file), cur_sample_rate, cur_sound_data)

    # Create a version concatenated N_REP times
    # Insert pause
    pause_data = np.zeros(int(pause*cur_sample_rate))
    data = np.concatenate([data, pause_data])
    data_concat = np.concatenate([data]*N_REP)
    trigger_concat = np.zeros(len(data_concat))
    trigger_concat[:N] = A_trigger
    cur_sound_data_concat = np.column_stack((data_concat, trigger_concat))

    # Save new files
    save_folder = os.path.join(thisDir, folder_output_concat, cur_wav_type)
    os.makedirs(save_folder, exist_ok=True)
    wavfile.write(os.path.join(save_folder, cur_wav_file), cur_sample_rate, cur_sound_data_concat)
    save_folder = os.path.join(thisDir, folder_output_concat_here, cur_wav_type)
    os.makedirs(save_folder, exist_ok=True)
    wavfile.write(os.path.join(save_folder, cur_wav_file), cur_sample_rate, cur_sound_data_concat)

print('Done!')