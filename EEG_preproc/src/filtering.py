#Filtering and resampling functions for EEG preprocessing pipeline
import mne

def filter_and_resample(raw, filter_cfg):

    notch_freqs = filter_cfg["notch_freqs"]
    l_freq = filter_cfg["l_freq"]
    h_freq = filter_cfg["h_freq"]

    filter_method = filter_cfg["method"]
    filter_phase = filter_cfg["phase"]

    resample_sfreq = filter_cfg["resample_sfreq"]
    # resample_method = filter_cfg["resample_method"]

    print("\n=== Filtering ===")

    raw.notch_filter(freqs=notch_freqs, picks="eeg")

    raw.filter(
        l_freq=l_freq,
        h_freq=h_freq,
        method=filter_method,
        phase=filter_phase,
        picks="eeg"
    )

    print("\n=== Resampling ===")

    raw.resample(
        resample_sfreq
        # method=resample_method
    )

    return raw