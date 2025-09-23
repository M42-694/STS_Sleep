import os
import numpy as np
from scipy.io import wavfile

# Paths
folder_input = '/Users/michelle.george/Desktop/Speech2Song/Scripts/speech2song_song_psychopy/input/stimuli'
folder_output_here = './input_new/stimuli'

# Ensure output directory exists
os.makedirs(folder_output_here, exist_ok=True)

# Get all WAV files recursively
wav_files = []
for root, dirs, files in os.walk(folder_input):
    for file in files:
        if file.lower().endswith('.wav') and not file.startswith('.'):
            wav_files.append(os.path.join(root, file))

print(f"Found {len(wav_files)} WAV files.")

# Helper to compute RMS energy
def rms(signal):
    return np.sqrt(np.mean(np.square(signal.astype(np.float64))))

# Process files
for wav_path in wav_files:
    sample_rate, data = wavfile.read(wav_path)
    filename = os.path.basename(wav_path)

    if data.ndim == 1:
        # Mono → stereo by duplication
        stereo_data = np.stack((data, data), axis=-1)
        print(f"{filename}: mono → stereo")
    elif data.ndim == 2 and data.shape[1] == 2:
        left, right = data[:, 0], data[:, 1]
        left_rms = rms(left)
        right_rms = rms(right)

        # Choose the channel with higher energy
        if left_rms > right_rms:
            stereo_data = np.stack((left, left), axis=-1)
            print(f"{filename}: stereo → L-to-both (L louder: {left_rms:.3f} > {right_rms:.3f})")
        else:
            stereo_data = np.stack((right, right), axis=-1)
            print(f"{filename}: stereo → R-to-both (R louder: {right_rms:.3f} > {left_rms:.3f})")
    else:
        print(f"{filename}: unsupported shape {data.shape}, skipping.")
        continue

    # Save fixed stereo file
    output_path = os.path.join(folder_output_here, filename)
    wavfile.write(output_path, sample_rate, stereo_data)

print("All files processed and stereo corrected.")


#checking sampling rate
file_path = AT0027.wav
sample_rate, data = wavfile.read(file_path)