#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 14:23:04 2025

@author: michelle.george
"""
import numpy as np
import h5py
from scipy.signal import welch, butter, filtfilt
from scipy.signal.windows import hamming
from utilities.Features import Fea_Extractor
# -- Helper functions from earlier sections ---
# spectral_entropy, comp_1f_slope, band_power, check_artifact




def main_feature_extraction(h5_file, dataset_path):
    """
    h5_file      : Path to 's12_n1.h5'
    dataset_path : Path inside HDF5 to the left EEG dataset,
                   e.g. '/s12_n1/EEGleft' or similar.
    """
    fs = 256  # sampling rate
    t_start_sec = 1400
    t_end_sec   = 2600
    # Convert to sample indices
    start_sample = int(t_start_sec * fs)
    end_sample   = int(t_end_sec * fs)
    
    # --- Load the EEG data from HDF5 ---
    with h5py.File(h5_file, 'r') as f:
        # dataset_path might be something like '/s12_n1/EEGleft'
        eeg_data = f[dataset_path][start_sample:end_sample]
        # 'eeg_data' is now a NumPy array with length: (2600-1400)*256
    
    # A minimal pre-processing before extracting EEG features

    # -- 1) Statistical Trimming --
    percen_1 = np.percentile(eeg_data, 1)
    percen_99 = np.percentile(eeg_data, 99)
    eeg_data = np.clip(eeg_data, percen_1, percen_99)

    # -- 2) Band-pass Filter Design --
    low_cutoff = 0.5  # Hz
    high_cutoff = 20.0  # Hz
    filter_order = 4

    nyquist = 0.5 * fs
    low = low_cutoff / nyquist
    high = high_cutoff / nyquist
    b, a = butter(filter_order, [low, high], btype='bandpass')
    EEG_Pre = filtfilt(b, a, eeg_data)


    # --- Define parameters for sliding window ---
    windowDuration = 10  # seconds
    stepDuration   = 1   # seconds
    windowLength = windowDuration * fs   # e.g., 2560
    stepSize     = stepDuration * fs     # e.g., 256
    
    # Example artifact intervals (in seconds).
    # Adjust these to your actual known artifact intervals.
    artifactIntervals = np.array([
        [200, 206],
        [308, 316],
        [439, 447]
    ])
    
    # Frequency bands: [1,4], [4,8], [8,10], [12,16]
    freq_bands = np.array([[1,4],[4,8],[8,10],[12,16]])
    band_names = ['Delta','Theta','Alpha','Sigma']
    num_bands  = freq_bands.shape[0]
    
    # How many windows total?
    n_samples = len(EEG_Pre)
    num_windows = (n_samples - windowLength)//stepSize + 1
    
    # Preallocate arrays
    band_power_vals = np.zeros((num_bands, num_windows))
    band_ratio_vals = np.zeros((num_bands, num_windows))
    spec_entropy_vals = np.zeros(num_windows)
    slope_vals        = np.zeros(num_windows)
    time_axis         = np.zeros(num_windows)
    
    # Welch parameters
    nperseg  = 2 * fs  # 2-second hamming window for each PSD estimate
    noverlap = nperseg // 2
    window   = hamming(nperseg)

    freq_range_for_slope = [2, 20]  # e.g. 2-20 Hz for 1/f slope
    # --- Sliding window loop ---
    for k in range(num_windows):
        idx_start = k*stepSize
        idx_end   = idx_start + windowLength
        segment   = EEG_Pre[idx_start:idx_end]
        
        # Time in seconds for the center of the window
        win_start_sec = t_start_sec + (idx_start / fs)
        win_end_sec   = t_start_sec + (idx_end   / fs)
        time_axis[k]  = (win_start_sec + win_end_sec)/2
        
        # If an artifact is detected in this time range, reuse previous values
        if k > 0 and Fea_Extractor.checkArtifact(win_start_sec, win_end_sec, artifactIntervals):
            band_power_vals[:,k]   = band_power_vals[:,k-1]
            band_ratio_vals[:,k]   = band_ratio_vals[:,k-1]
            spec_entropy_vals[k]   = spec_entropy_vals[k-1]
            slope_vals[k]          = slope_vals[k-1]
            continue

        # Compute PSD via Welch
        freqs, pxx = welch(
            segment,
            fs=fs,
            window=window,
            noverlap=noverlap,
            nperseg=nperseg,
            scaling='density'
        )
        
        # For each band, sum the PSD
        for b_idx in range(num_bands):
            bp = Fea_Extractor.cal_freq_power(pxx, freqs, freq_bands[b_idx])
            band_power_vals[b_idx, k] = bp
        
        total_power = np.sum(band_power_vals[:, k])
        if total_power > 0:
            band_ratio_vals[:, k] = band_power_vals[:, k] / total_power
        
        spec_entropy_vals[k] = Fea_Extractor.spectral_entropy(pxx)
        slope_vals[k]        = Fea_Extractor.comp_1f_slope(freqs, pxx, freq_range_for_slope)
    
    # Done! You now have band_power_vals, band_ratio_vals, spectral_entropy_vals, slope_vals, time_axis
    
    return (time_axis,
            band_power_vals,
            band_ratio_vals,
            spec_entropy_vals,
            slope_vals)

if __name__ == "__main__":
    # Example usage:
    h5_file = "./data/s12_n1.h5"
    dataset_path = "/s12_n1/channels/EEG L"  # <-- Adjust to the actual path found via explore_hdf5_structure
    (time_axis,
     band_power_vals,
     band_ratio_vals,
     spec_entropy_vals,
     slope_vals) = main_feature_extraction(h5_file, dataset_path)

    # You can now plot or analyze the returned arrays as you like!
    # e.g., print a quick summary
    print("Time axis length:", len(time_axis))
    print("BandPower shape:", band_power_vals.shape)
    print("Spec entropy shape:", spec_entropy_vals.shape)
    print("Slope shape:", slope_vals.shape)
    # Organize
    features_dict = Fea_Extractor.organize_features(
        time_axis,
        band_power_vals,
        band_ratio_vals,
        spec_entropy_vals,
        slope_vals
    )
    filename = './data/Feature_Donders/s12_n1/features.json'
    Fea_Extractor.save_features(features_dict, filename)


