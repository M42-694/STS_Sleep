import os
import re
import numpy as np
from scipy.io import wavfile

# Parameters
sampleRate = 44100  # Hz
N_REP = 8
pause = 0.5  # seconds
types = ["song", "speech"]

# Input/output paths
folder_input = '/Users/michelle.george/Desktop/Speech2Song/Scripts/speech2song_psychopy/input/stimuli'
folder_output_root = './input_new'
folder_output_stereo = os.path.join(folder_output_root, 'stimuli')
folder_output_repeated = os.path.join(folder_output_root, f'rep_concatenated_{N_REP}times')

# --- Helper Functions ---

# Extract just the number from the filename
def extract_number(filename):
    match = re.search(r'(\d+)', filename)
    return match.group(1) if match else os.path.splitext(filename)[0]

# Normalize audio to peak amplitude
def normalize(signal, target_peak=0.99):
    max_val = np.max(np.abs(signal.astype(np.float64)))
    if max_val == 0:
        return signal
    factor = target_peak / max_val
    return (signal * factor).astype(signal.dtype)

# Choose the real audio channel by comparing activity duration (not amplitude)
def choose_real_channel(left, right, threshold=0.001):
    def active_duration(signal):
        abs_signal = np.abs(signal.astype(np.float64))
        return np.sum(abs_signal > threshold)

    dur_left = active_duration(left)
    dur_right = active_duration(right)

    if dur_left >= dur_right:
        return np.stack((left, left), axis=-1), "left"
    else:
        return np.stack((right, right), axis=-1), "right"

# --- Prepare output folders ---
for stim_type in types:
    os.makedirs(os.path.join(folder_output_stereo, stim_type), exist_ok=True)
    os.makedirs(os.path.join(folder_output_repeated, stim_type), exist_ok=True)

# --- Main processing loop ---
for stim_type in types:
    input_path = os.path.join(folder_input, stim_type)
    files = [f for f in os.listdir(input_path) if f.lower().endswith('.wav') and not f.startswith(".")]

    for filename in files:
        file_path = os.path.join(input_path, filename)
        print(f"🔊 Processing {stim_type}/{filename}")

        # Read file
        sr, data = wavfile.read(file_path)
        if sr != sampleRate:
            raise ValueError(f"Sample rate mismatch in {filename}: expected {sampleRate}, got {sr}")

        # Ensure stereo: mono → stereo or pseudo-stereo fix
        if data.ndim == 1:
            data = np.stack((data, data), axis=-1)
            print("   → Converted mono to stereo")
        elif data.ndim == 2:
            left, right = data[:, 0], data[:, 1]
            data, chosen = choose_real_channel(left, right)
            print(f"   → Stereo: copied {chosen} channel (longer activity)")

        # Normalize
        data = normalize(data)
        print("   → Normalized to consistent peak level")

        # Generate name based on number
        number = extract_number(filename)
        output_name = f"{number}.wav"

        # Save stereo version
        stereo_out_path = os.path.join(folder_output_stereo, stim_type, output_name)
        wavfile.write(stereo_out_path, sampleRate, data)
        print(f"   → Saved stereo to {stereo_out_path}")

        # Create silence and repeated version
        silence_samples = int(sampleRate * pause)
        silence = np.zeros((silence_samples, 2), dtype=data.dtype)

        repeated = []
        for _ in range(N_REP):
            repeated.append(data)
            repeated.append(silence)
        looped_data = np.concatenate(repeated)

        # Save repeated version
        repeated_out_path = os.path.join(folder_output_repeated, stim_type, output_name)
        wavfile.write(repeated_out_path, sampleRate, looped_data)
        print(f"   → Saved repeated version to {repeated_out_path}")

print("\n✅ All files processed successfully.")
