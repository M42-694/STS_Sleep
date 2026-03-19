import numpy as np
import pandas as pd

import mne


def create_fixed_length_epochs(raw_phase, segment_length):

    duration = raw_phase.times[-1]

    if duration < segment_length:
        raise RuntimeError(
            f"Segment too short for epoching ({duration:.2f}s)"
        )

    epochs = mne.make_fixed_length_epochs(
        raw_phase,
        duration=segment_length,
        preload=True,
        overlap=0
    )

    if len(epochs) == 0:
        raise RuntimeError("Fixed epoching produced zero epochs")

    return epochs

def create_sleep_epochs(raw_nap, events, event_id, segment_length):

    epochs = mne.Epochs(
        raw_nap,
        events,
        event_id=event_id,
        tmin=0,
        tmax=segment_length,
        baseline=None,
        preload=True
    )

    return epochs


def segment_sleep_annotations_to_events(
    raw,
    sleep_annotations,
    segment_length=10.0,
    group_map=None,
):

    sfreq = raw.info["sfreq"]

    events = []
    event_id = {}
    current_id = 1

    for annot in sleep_annotations:

        onset = annot["onset"]
        duration = annot["duration"]
        label = annot["description"]

        if group_map:
            label = group_map.get(label)
            if label is None:
                continue

        if label not in event_id:
            event_id[label] = current_id
            current_id += 1

        # number of segments within this sleep stage
        n_segments = int(np.floor(duration / segment_length))

        for i in range(n_segments):

            seg_onset = onset + i * segment_length
            sample = int(round(seg_onset * sfreq))

            events.append([sample, 0, event_id[label]])

    return np.array(events, dtype=int), event_id


def check_epoch_groups(epochs):

    counts = {k: len(epochs[k]) for k in epochs.event_id}

    print("Epoch counts:", counts)

    if sum(counts.values()) == 0:
        raise RuntimeError("No epochs created")

    return counts